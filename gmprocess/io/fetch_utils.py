# stdlib imports
import os.path
import json
import logging
import warnings
import glob
import re

# third party imports
from obspy.geodetics.base import locations2degrees
from obspy.taup import TauPyModel
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import pandas as pd
from openpyxl import load_workbook
import yaml
import numpy as np
from impactutils.mapping.city import Cities
from impactutils.mapping.mercatormap import MercatorMap
from impactutils.mapping.scalebar import draw_scale
from cartopy import feature as cfeature

# local imports
from gmprocess.utils.event import get_event_object
from gmprocess.utils.config import get_config, update_dict
from gmprocess.io.stream import streams_to_dataframe
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.read_directory import directory_to_streams
from gmprocess.io.global_fetcher import fetch_data
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.event import ScalarEvent
from gmprocess.utils.constants import RUPTURE_FILE, WORKSPACE_NAME

TIMEFMT2 = '%Y-%m-%dT%H:%M:%S.%f'


OCEAN_COLOR = '#96e8ff'
LAND_COLOR = '#ededaf'
PASSED_COLOR = '#00ac00'
FAILED_COLOR = '#ff2222'

MAP_PADDING = 1.1  # Station map padding value

UNITS = {'PGA': '%g',
         'PGV': 'cm/s',
         'SA': '%g'
         }

FLOAT_PATTERN = r'[-+]?[0-9]*\.?[0-9]+'


def download(event, event_dir, config, directory, create_workspace=True):
    """Download data or load data from local directory, turn into Streams.

    Args:
        event (ScalarEvent):
            Object containing basic event hypocenter, origin time, magnitude.
        event_dir (str):
            Path where raw directory should be created (if downloading).
        config (dict):
            Dictionary with gmprocess configuration information.
        directory (str):
            Path where data already exists. Must be organized in a 'raw'
            directory, within directories with names as the event ids. For
            example, if `directory` is 'proj_dir' and you have data for
            event id 'abc123' then the raw data to be read in should be
            located in `proj_dir/abc123/raw/`.
        create_workspace (bool):
            Create workspace file?

    Returns:
        tuple:
            - StreamWorkspace: Contains the event and raw streams.
            - str: Name of workspace HDF file.
            - StreamCollection: Raw data StationStreams.
            - str: Path to the rupture file.
    """
    # Make raw directory
    rawdir = get_rawdir(event_dir)

    if directory is None:
        tcollection, terrors = fetch_data(
            event.time.datetime,
            event.latitude,
            event.longitude,
            event.depth_km,
            event.magnitude,
            config=config,
            rawdir=rawdir)
        # create an event.json file in each event directory,
        # in case user is simply downloading for now
        create_event_file(event, event_dir)
        rup_file = get_rupture_file(event_dir)
    else:
        # Make raw directory
        in_event_dir = os.path.join(directory, event.id)
        rup_file = get_rupture_file(in_event_dir)
        in_raw_dir = get_rawdir(in_event_dir)
        logging.debug('in_raw_dir: %s' % in_raw_dir)
        streams, bad, terrors = directory_to_streams(in_raw_dir)
        logging.debug('streams:')
        logging.debug(streams)
        tcollection = StreamCollection(streams, **config['duplicate'])
        create_event_file(event, event_dir)
    logging.debug('tcollection.describe():')
    logging.debug(tcollection.describe())

    # Plot the raw waveforms
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        pngfiles = glob.glob(os.path.join(rawdir, '*.png'))
        if not len(pngfiles):
            plot_raw(rawdir, tcollection, event)

    if create_workspace:
        # Create the workspace file and put the unprocessed waveforms in it
        workname = os.path.join(event_dir, WORKSPACE_NAME)

        # Remove any existing workspace file
        if os.path.isfile(workname):
            os.remove(workname)

        workspace = StreamWorkspace(workname)
        workspace.addEvent(event)
        logging.debug('workspace.dataset.events:')
        logging.debug(workspace.dataset.events)
        workspace.addStreams(event, tcollection, label='unprocessed')
        logging.debug('workspace.dataset.waveforms.list():')
        logging.debug(workspace.dataset.waveforms.list())
    else:
        workspace = None
        workname = None
    return (workspace, workname, tcollection, rup_file)


def parse_event_file(eventfile):
    """Parse text file containing basic event information.

    Files can contain:
        - one column, in which case that column
          contains ComCat event IDs.
        - Seven columns, in which case those columns should be:
          - id: any string (no spaces)
          - time: Any ISO standard for date/time.
          - lat: Earthquake latitude in decimal degrees.
          - lon: Earthquake longitude in decimal degrees.
          - depth: Earthquake longitude in kilometers.
          - magnitude: Earthquake magnitude.
          - magnitude_type: Earthquake magnitude type.

    NB: THERE SHOULD NOT BE ANY HEADERS ON THIS FILE!

    Args:
        eventfile (str):
            Path to event text file

    Returns:
        list: ScalarEvent objects constructed from list of event information.

    """
    df = pd.read_csv(eventfile, sep=',', header=None)
    nrows, ncols = df.shape
    events = []
    if ncols == 1:
        df.columns = ['eventid']
        for idx, row in df.iterrows():
            event = get_event_object(row['eventid'])
            events.append(event)
    elif ncols == 7:
        df.columns = ['id', 'time', 'lat', 'lon', 'depth', 'magnitude',
                      'magnitude_type']
        df['time'] = pd.to_datetime(df['time'])
        for idx, row in df.iterrows():
            rowdict = row.to_dict()
            event = get_event_object(rowdict)
            events.append(event)
    else:
        return None
    return events


def draw_stations_map(pstreams, event, event_dir):
    # draw map of stations and cities and stuff
    lats = np.array([stream[0].stats.coordinates['latitude']
                     for stream in pstreams])
    lons = np.array([stream[0].stats.coordinates['longitude']
                     for stream in pstreams])
    cy = event.latitude
    cx = event.longitude
    xmin = lons.min()
    xmax = lons.max()
    ymin = lats.min()
    ymax = lats.max()

    diff_x = max(abs(cx - xmin), abs(cx - xmax), 1)
    diff_y = max(abs(cy - ymin), abs(cy - ymax), 1)

    xmax = cx + MAP_PADDING * diff_x
    xmin = cx - MAP_PADDING * diff_x
    ymax = cy + MAP_PADDING * diff_y
    ymin = cy - MAP_PADDING * diff_y

    bounds = (xmin, xmax, ymin, ymax)
    figsize = (10, 10)
    cities = Cities.fromDefault()
    mmap = MercatorMap(bounds, figsize, cities)
    mmap.drawCities(draw_dots=True)
    ax = mmap.axes
    draw_scale(ax)
    ax.plot(cx, cy, 'r*', markersize=16,
            transform=mmap.geoproj, zorder=8)
    status = [FAILED_COLOR if np.any([trace.hasParameter("failure")
                                      for trace in stream]) else PASSED_COLOR
              for stream in pstreams]
    ax.scatter(lons, lats, c=status, marker='^', edgecolors='k',
               transform=mmap.geoproj, zorder=100, s=48)

    passed_marker = mlines.Line2D(
        [], [], color=PASSED_COLOR, marker='^',
        markeredgecolor='k', markersize=12,
        label='Passed station', linestyle='None')
    failed_marker = mlines.Line2D(
        [], [], color=FAILED_COLOR, marker='^',
        markeredgecolor='k', markersize=12,
        label='Failed station', linestyle='None')
    earthquake_marker = mlines.Line2D(
        [], [], color='red', marker='*',
        markersize=12,
        label='Earthquake Epicenter',
        linestyle='None')
    ax.legend(handles=[passed_marker, failed_marker, earthquake_marker],
              fontsize=12)

    scale = '50m'
    land = cfeature.NaturalEarthFeature(
        category='physical',
        name='land',
        scale=scale,
        facecolor=LAND_COLOR)
    ocean = cfeature.NaturalEarthFeature(
        category='physical',
        name='ocean',
        scale=scale,
        facecolor=OCEAN_COLOR)
    ax.add_feature(land)
    ax.add_feature(ocean)
    ax.coastlines(resolution=scale, zorder=10, linewidth=1)
    mapfile = os.path.join(event_dir, 'stations_map.png')
    plt.savefig(mapfile)
    return mapfile


def get_event_files(directory):
    """Get list of event.json files found underneath a data directory.

    Args:
        directory (str):
            Path to directory containing input raw data, where
            subdirectories must be event directories containing
            event.json files, where the id in that file matches
            the directory under which it is found.
    Returns:
        List of event.json files.
    """
    eventfiles = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name == 'event.json':
                fullname = os.path.join(root, name)
                eventfiles.append(fullname)
    return eventfiles


def read_event_json_files(eventfiles):
    """Read event.json file and return ScalarEvent object.

    Args:
        eventfiles (list):
            Event.json files to be read.
    Returns:
        list: ScalarEvent objects.

    """
    events = []
    for eventfile in eventfiles:
        with open(eventfile, 'rt', encoding='utf-8') as f:
            eventdict = json.load(f)
            event = get_event_object(eventdict)
            events.append(event)
    return events


def get_events(eventids, textfile, eventinfo, directory,
               outdir=None):
    """Find the list of events.

    Args:
        eventids (list or None):
            List of ComCat event IDs.
        textfile (str or None):
            Path to text file containing event IDs or info.
        eventinfo (list or None):
            List containing:
                - id Any string, no spaces.
                - time Any ISO-compatible date/time string.
                - latitude Latitude in decimal degrees.
                - longitude Longitude in decimal degrees.
                - depth Depth in kilometers.
                - magnitude Earthquake magnitude.
                - magnitude_type Earthquake magnitude type.
        directory (str):
            Path to a directory containing event subdirectories, each
            containing an event.json file, where the ID in the json file
            matches the subdirectory containing it.
        outdir (str):
            Output directory.

    Returns:
        list: ScalarEvent objects.

    """
    events = []
    if eventids is not None:
        # Get list of events from directory if it has been provided
        tevents = []
        if directory is not None:
            tevents = events_from_directory(directory)
        elif outdir is not None:
            tevents = events_from_directory(outdir)
        for eventid in eventids:
            if len(tevents) and eventid in tevents:
                event = [e for e in tevents if e.id == eventid][0]
            else:
                # This connects to comcat to get event, does not check for a
                # local json file
                event = get_event_object(eventid)
            events.append(event)
    elif textfile is not None:
        events = parse_event_file(textfile)
    elif eventinfo is not None:
        eid = eventinfo[0]
        time = eventinfo[1]
        lat = float(eventinfo[2])
        lon = float(eventinfo[3])
        dep = float(eventinfo[4])
        mag = float(eventinfo[5])
        mag_type = str(eventinfo[6])
        event = ScalarEvent()
        event.fromParams(eid, time, lat, lon, dep, mag, mag_type)
        events = [event]
    elif directory is not None:
        events = events_from_directory(directory)
    elif outdir is not None:
        events = events_from_directory(outdir)
    return events


def events_from_directory(dir):
    events = []
    eventfiles = get_event_files(dir)
    if len(eventfiles):
        events = read_event_json_files(eventfiles)
    else:
        eventids = [f for f in os.listdir(dir) if not f.startswith('.')]
        for eventid in eventids:
            try:
                event = get_event_object(eventid)
                events.append(event)

                # If the event ID has been updated, make sure to rename
                # the source folder and issue a warning to the user
                if event.id != eventid:
                    old_dir = os.path.join(dir, eventid)
                    new_dir = os.path.join(dir, event.id)
                    os.rename(old_dir, new_dir)
                    logging.warn('Directory %s has been renamed to %s.' %
                                 (old_dir, new_dir))
            except BaseException:
                logging.warning(
                    'Could not get info for event id: %s' % eventid)

    return events


def create_event_file(event, event_dir):
    """Write event.json file in event_dir.

    Args:
        event (ScalarEvent):
            Input event object.
        event_dir (str):
            Directory where event.json should be written.
    """
    # create event.json file in each directory
    edict = {
        'id': event.id,
        'time': event.time.strftime(TIMEFMT2),
        'lat': event.latitude,
        'lon': event.longitude,
        'depth': event.depth_km,
        'magnitude': event.magnitude,
        'magnitude_type': event.magnitude_type
    }
    eventfile = os.path.join(event_dir, 'event.json')
    with open(eventfile, 'wt', encoding='utf-8') as f:
        json.dump(edict, f)


def get_rawdir(event_dir):
    """Find or create raw directory if necessary.

    Args:
        event_dir (str):
            Directory where raw directory will be found or created.
    """
    rawdir = os.path.join(event_dir, 'raw')
    if not os.path.exists(rawdir):
        os.makedirs(rawdir)
    return rawdir


def save_shakemap_amps(processed, event, event_dir):
    """Write ShakeMap peak amplitudes to Excel file and ShakeMap JSON.

    Args:
        processed (StreamCollection):
            Processed waveforms.
        event (ScalarEvent):
            Event object.
        event_dir (str):
            Directory where peak amps should be written.

    Returns:
        str: Path to output amps spreadsheet.
    """
    ampfile_name = None
    if processed.n_passed:
        dataframe = streams_to_dataframe(
            processed, event=event)
        ampfile_name = os.path.join(event_dir, 'shakemap.xlsx')

        # saving with index=False not supported by pandas
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
        # somehow pandas inserted an extra row between sub-headings and
        # the beginning of the data. Delete that row.
        ws.delete_rows(4)
        wb.save(ampfile_name)

        # get shakemap json, save to output directory
        jsonfile = os.path.join(event_dir, 'gmprocess_dat.json')
        jsonstr = get_shakemap_json(dataframe)
        with open(jsonfile, 'wt', encoding='utf-8') as fp:
            fp.write(jsonstr)

    return (ampfile_name, jsonfile)


def get_shakemap_json(dataframe):
    json_dict = {'type': 'FeatureCollection'}
    features = []
    for idx, row in dataframe.iterrows():
        feature = {'type': 'Feature'}
        # the columns without a sub-header need .iloc to reference value
        lon = row['LON'].iloc[0]
        lat = row['LAT'].iloc[0]
        station = row['STATION'].iloc[0]
        network = row["NETID"].iloc[0]
        name = row["NAME"].iloc[0]
        source = row["SOURCE"].iloc[0]
        geometry = {
            'type': 'Point',
            'coordinates': (lon, lat)
        }
        sid = f'{network}.{station}'
        feature['id'] = sid
        feature['geometry'] = geometry
        props = {}
        props['code'] = station
        props['name'] = name
        props['source'] = source
        props['network'] = network

        channeldict = {}
        channels = []
        channeldict['name'] = 'H1'
        amplitudes = []
        for ampcol, value in row['GREATER_OF_TWO_HORIZONTALS'].iteritems():
            ampdict = {}
            imtname = ampcol.lower()
            if 'SA' in ampcol:
                # pull apart SA name, set period to 1 digit precision
                period = float(re.search(FLOAT_PATTERN, imtname).group())
                imtname = f'sa({period:.1f})'
                units = UNITS['SA']
            else:
                units = UNITS[ampcol]
            ampdict['name'] = imtname
            ampdict['value'] = value
            ampdict['units'] = units
            ampdict['ln_sigma'] = 0.0
            ampdict['flag'] = 0
            amplitudes.append(ampdict)
        channeldict['amplitudes'] = amplitudes
        channels.append(channeldict)

        props['channels'] = channels
        feature['properties'] = props
        features.append(feature)
    json_dict['features'] = features
    json_str = json.dumps(json_dict)
    return json_str


def update_config(custom_cfg_file):
    """Merge custom config with default.

    Args:
        custom_cfg_file (str):
            Path to custom config.

    Returns:
        dict: Merged config dictionary.

    """
    config = get_config()

    if not os.path.isfile(custom_cfg_file):
        return config
    try:
        with open(custom_cfg_file, 'rt', encoding='utf-8') as f:
            custom_cfg = yaml.load(f, Loader=yaml.FullLoader)
            update_dict(config, custom_cfg)
    except yaml.parser.ParserError:
        return None

    return config


def plot_raw(rawdir, tcollection, event):
    """Make PNG plots of a collection of raw waveforms.

    Args:
        rawdir (str):
            Directory where PNG files should be saved.
        tcollection (StreamCollection):
            Sequence of streams.
        event (ScalarEvent):
            Event object.

    """
    model = TauPyModel(model="iasp91")
    source_depth = event.depth_km
    if source_depth < 0:
        source_depth = 0
    eqlat = event.latitude
    eqlon = event.longitude
    for stream in tcollection:
        stlat = stream[0].stats.coordinates['latitude']
        stlon = stream[0].stats.coordinates['longitude']
        dist = float(locations2degrees(eqlat, eqlon, stlat, stlon))
        try:
            arrivals = model.get_travel_times(
                source_depth_in_km=source_depth,
                distance_in_degree=dist,
                phase_list=['P', 'p', 'Pn'])
            arrival = arrivals[0]
            arrival_time = arrival.time
        except Exception as e:
            fmt = ('Exception "%s" generated by get_travel_times() dist=%.3f '
                   'depth=%.1f')
            logging.warning(fmt % (str(e), dist, source_depth))
            arrival_time = 0.0
        ptime = arrival_time + (event.time - stream[0].stats.starttime)
        outfile = os.path.join(rawdir, '%s.png' % stream.get_id())

        fig, axeslist = plt.subplots(nrows=3, ncols=1, figsize=(12, 6))
        for ax, trace in zip(axeslist, stream):
            ax.plot(trace.times(), trace.data, color='k')
            ax.set_xlabel('seconds since start of trace')
            ax.set_title('')
            ax.axvline(ptime, color='r')
            ax.set_xlim(left=0, right=trace.times()[-1])
            legstr = '%s.%s.%s.%s' % (
                trace.stats.network,
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


def get_rupture_file(event_dir):
    """Get the path to the rupture file, or None if there is not rupture file.

    Args:
        event_dir (str): Event directory.

    Returns:
        str: Path to the rupture file. Returns None if no rupture file exists.
    """
    rupture_file = os.path.join(event_dir, RUPTURE_FILE)
    if not os.path.exists(rupture_file):
        rupture_file = None
    return rupture_file
