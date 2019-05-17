# stdlib imports
import os.path
import json
import warnings

# third party imports
from obspy.geodetics.base import locations2degrees
from obspy.taup import TauPyModel
import matplotlib.pyplot as plt
import pandas as pd
from openpyxl import load_workbook
import yaml
from h5py.h5py_warnings import H5pyDeprecationWarning

# local imports
from gmprocess.event import get_event_object
from gmprocess.config import get_config, update_dict
from gmprocess.stream import streams_to_dataframe
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.read_directory import directory_to_streams
from gmprocess.io.global_fetcher import fetch_data
from gmprocess.streamcollection import StreamCollection

TIMEFMT2 = '%Y-%m-%dT%H:%M:%S.%f'


def download(event, event_dir, config, directory):
    # generate the raw directory
    rawdir = get_rawdir(event_dir, event)

    if directory is None:
        tcollection, terrors = fetch_data(event.time.datetime,
                                          event.latitude,
                                          event.longitude,
                                          event.depth_km,
                                          event.magnitude,
                                          config=config,
                                          rawdir=rawdir)
        # create an event.json file in each event directory,
        # in case user is simply downloading for now
        create_event_file(event, event_dir)
    else:
        input_eventdir = os.path.join(event_dir, 'raw')
        streams, bad, terrors = directory_to_streams(input_eventdir)
        tcollection = StreamCollection(streams)

    # plot the raw waveforms
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        pngfiles = glob.glob(os.path.join(rawdir, '*.png'))
        if not len(pngfiles):
            plot_raw(rawdir, tcollection, event)

    # create the workspace file and put the unprocessed waveforms in it
    workname = os.path.join(event_dir, 'workspace.hdf')
    if os.path.isfile(workname):
        os.remove(workname)
    workspace = StreamWorkspace(workname)
    workspace.addEvent(event)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=H5pyDeprecationWarning)
        workspace.addStreams(event, tcollection, label='unprocessed')

    return (workspace, workname, tcollection)


def parse_event_file(eventfile):
    df = pd.read_csv(eventfile, sep=',', header=None)
    nrows, ncols = df.shape
    events = []
    if ncols == 1:
        df.columns = ['eventid']
        for idx, row in df.iterrows():
            event = get_event_object(row['eventid'])
            events.append(event)
    elif ncols == 6:
        df.columns = ['id', 'time', 'lat', 'lon', 'depth', 'magnitude']
        df['time'] = pd.to_datetime(df['time'])
        for idx, row in df.iterrows():
            rowdict = row.to_dict()
            event = get_event_object(rowdict)
            events.append(event)
    else:
        return None
    return events


def get_event_files(directory):
    eventfiles = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name == 'event.json':
                fullname = os.path.join(root, name)
                eventfiles.append(fullname)
    return eventfiles


def read_event_json_files(eventfiles):
    events = []
    for eventfile in eventfiles:
        with open(eventfile, 'rt') as f:
            eventdict = json.load(f)
            # eventdict['depth'] *= 1000
            event = get_event_object(eventdict)
            events.append(event)
    return events


def get_events(eventids, textfile, eventinfo, directory):
    events = []
    if eventids:
        for eventid in eventids:
            event = get_event_object(eventid)
            events.append(event)
    elif textfile:
        events = parse_event_file(textfile)
    elif directory:
        eventfiles = get_event_files(directory)
        if not len(eventfiles):
            eventids = os.listdir(directory)
            try:
                for eventid in eventids:
                    event = get_event_object(eventid)
                    events.append(event)
            except Exception:
                events = []
        else:
            events = read_event_json_files(eventfiles)
    return events


def create_event_file(event, event_dir):
    # create event.json file in each directory
    edict = {'id': event.id,
             'time': event.time.strftime(TIMEFMT2),
             'lat': event.latitude,
             'lon': event.longitude,
             'depth': event.depth_km,
             'magnitude': event.magnitude}
    eventfile = os.path.join(event_dir, 'event.json')
    with open(eventfile, 'wt') as f:
        json.dump(edict, f)


def get_rawdir(event_dir, event):
    rawdir = os.path.join(event_dir, 'raw')
    if not os.path.exists(rawdir):
        os.makedirs(rawdir)
    return rawdir


def save_shakemap_amps(processed, event, event_dir):
    ampfile_name = None
    if processed.n_passed:
        dataframe = streams_to_dataframe(processed,
                                         event=event)
        ampfile_name = os.path.join(event_dir, 'shakemap.xlsx')

        dataframe.to_excel(ampfile_name)

        wb = load_workbook(ampfile_name)
        ws = wb.active
        # TODO: This ws.append() fails sometimes. Going back to using pandas.
        # for r in dataframe_to_rows(dataframe, index=True, header=True):
        #     try:
        #         ws.append(r)
        #     except Exception as e:
        #         x = 1

        # we don't need the index column, so we'll delete it here
        ws.delete_cols(1)
        ws.insert_rows(1)
        ws['A1'] = 'REFERENCE'
        ws['B1'] = dataframe['SOURCE'].iloc[0]
        wb.save(ampfile_name)

    return ampfile_name


def update_config(custom_cfg_file):
    config = get_config()

    if not os.path.isfile(custom_cfg_file):
        return config
    try:
        with open(custom_cfg_file, 'rt') as f:
            custom_cfg = yaml.load(f, Loader=yaml.FullLoader)
            update_dict(config, custom_cfg)
    except yaml.parser.ParserError as pe:
        return None

    return config


def plot_raw(rawdir, tcollection, event):
    model = TauPyModel(model="iasp91")
    source_depth = event.depth_km
    eqlat = event.latitude
    eqlon = event.longitude
    for stream in tcollection:
        stlat = stream[0].stats.coordinates['latitude']
        stlon = stream[0].stats.coordinates['longitude']
        dist = locations2degrees(eqlat, eqlon, stlat, stlon)
        arrivals = model.get_travel_times(source_depth_in_km=source_depth,
                                          distance_in_degree=dist, phase_list=['P', 'p', 'Pn'])
        arrival = arrivals[0]
        arrival_time = arrival.time
        ptime = arrival_time + (event.time - stream[0].stats.starttime)
        outfile = os.path.join(rawdir, '%s.png' % stream.get_id())

        fig, axeslist = plt.subplots(nrows=3, ncols=1, figsize=(12, 6))
        for ax, trace in zip(axeslist, stream):
            ax.plot(trace.times(), trace.data, color='k')
            ax.set_xlabel('seconds since start of trace')
            ax.set_title('')
            ax.axvline(ptime, color='r')
            ax.set_xlim(left=0, right=trace.times()[-1])
            legstr = '%s.%s.%s.%s' % (trace.stats.network,
                                      trace.stats.station,
                                      trace.stats.location,
                                      trace.stats.channel)
            ax.legend(labels=[legstr], frameon=True, loc='upper left')
            tbefore = event.time + arrival_time < trace.stats.starttime + 1.0
            tafter = event.time + arrival_time > trace.stats.endtime - 1.0
            if tbefore or tafter:
                legstr = 'P arrival time %.1f seconds' % ptime
                left, right = ax.get_xlim()
                xloc = left + (right - left) / 20
                bottom, top = ax.get_ylim()
                yloc = bottom + (top - bottom) / 10
                ax.text(xloc, yloc, legstr, color='r')
        plt.savefig(outfile, bbox_inches='tight')
        plt.close()
