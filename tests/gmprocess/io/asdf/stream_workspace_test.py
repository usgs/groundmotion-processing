#!/usr/bin/env python

import os
import shutil
import time
import tempfile
import warnings

from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.read import read_data
from gmprocess.processing import process_streams
from gmprocess.config import get_config
from gmprocess.io.test_utils import read_data_dir
from gmprocess.event import get_event_object
from gmprocess.streamcollection import StreamCollection
from gmprocess.io.fdsn import request_raw_waveforms
from gmprocess.event import get_event_dict

from h5py.h5py_warnings import H5pyDeprecationWarning
from yaml import YAMLLoadWarning

import numpy as np
import pandas as pd


def compare_streams(instream, outstream):
    pkeys = instream[0].getParameterKeys()
    for key in pkeys:
        if not outstream[0].hasParameter(key):
            assert 1 == 2
        invalue = instream[0].getParameter(key)
        outvalue = outstream[0].getParameter(key)
        if isinstance(invalue, (int, float, str)):
            assert invalue == outvalue
        if isinstance(invalue, dict):
            # Currenlty, we also have dictionaries with list of floats
            # as entries. This could get more complicated if we start
            # storing a wider variety of data structures...
            for k, v in invalue.items():
                if isinstance(v, list):
                    inarray = np.array(v)
                    outarray = np.array(outvalue[k])
                    np.testing.assert_allclose(inarray, outarray)

    # compare the provenance from the input processed stream
    # to it's output equivalent
    pkeys = instream[0].getProvenanceKeys()
    for key in pkeys:
        inprov = instream[0].getProvenance(key)[0]
        outprov = outstream[0].getProvenance(key)[0]
        for key, invalue in inprov.items():
            outvalue = outprov[key]
            if isinstance(invalue, (int, float, str)):
                assert invalue == outvalue
            else:
                assert np.abs(invalue - outvalue) < 1


def test_workspace():
    eventid = 'us1000778i'
    datafiles, origin = read_data_dir('geonet', eventid, '*.V1A')
    event = get_event_object(origin)
    tdir = tempfile.mkdtemp()
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=H5pyDeprecationWarning)
            warnings.filterwarnings("ignore", category=YAMLLoadWarning)
            warnings.filterwarnings("ignore", category=FutureWarning)
            config = get_config()
            tfile = os.path.join(tdir, 'test.hdf')
            raw_streams = []
            for dfile in datafiles:
                raw_streams += read_data(dfile)

            workspace = StreamWorkspace(tfile)
            t1 = time.time()
            workspace.addStreams(event, raw_streams, label='raw')
            t2 = time.time()
            print('Adding %i streams took %.2f seconds' %
                  (len(raw_streams), (t2 - t1)))

            str_repr = workspace.__repr__()
            assert str_repr == 'Events: 1 Stations: 3 Streams: 3'

            eventobj = workspace.getEvent(eventid)
            assert eventobj.origins[0].latitude == event.origins[0].latitude
            assert eventobj.magnitudes[0].mag == event.magnitudes[0].mag

            stations = workspace.getStations()
            assert sorted(stations) == ['hses', 'thz', 'wtmc']

            stations = workspace.getStations(eventid=eventid)
            assert sorted(stations) == ['hses', 'thz', 'wtmc']

            # test retrieving tags for an event that doesn't exist
            try:
                workspace.getStreamTags('foo')
            except KeyError:
                assert 1 == 1

            # test retrieving event that doesn't exist
            try:
                workspace.getEvent('foo')
            except KeyError:
                assert 1 == 1

            instream = None
            for stream in raw_streams:
                if stream[0].stats.station.lower() == 'hses':
                    instream = stream
                    break
            if instream is None:
                assert 1 == 2
            outstream = workspace.getStreams(eventid,
                                             stations=['hses'],
                                             labels=['raw'])[0]
            compare_streams(instream, outstream)

            label_summary = workspace.summarizeLabels()
            assert label_summary.iloc[0]['Label'] == 'raw'
            assert label_summary.iloc[0]['Software'] == 'gmprocess'

            sc = StreamCollection(raw_streams)
            processed_streams = process_streams(sc, origin, config=config)
            workspace.addStreams(event, processed_streams, 'processed')

            idlist = workspace.getEventIds()
            assert idlist[0] == eventid

            event_tags = workspace.getStreamTags(eventid)
            assert sorted(event_tags) == ['hses_processed', 'hses_raw',
                                          'thz_processed', 'thz_raw',
                                          'wtmc_processed', 'wtmc_raw']
            outstream = workspace.getStreams(eventid,
                                             stations=['hses'],
                                             labels=['processed'])[0]

            provenance = workspace.getProvenance(eventid, labels=['processed'])
            first_row = pd.Series({'Record': 'NZ.HSES.HN1',
                                   'Processing Step': 'Remove Response',
                                   'Step Attribute': 'input_units',
                                   'Attribute Value': 'counts'})

            last_row = pd.Series({'Record': 'NZ.WTMC.HNZ',
                                  'Processing Step': 'Detrend',
                                  'Step Attribute': 'detrending_method',
                                  'Attribute Value': 'baseline_sixth_order'})
            assert provenance.iloc[0].equals(first_row)
            assert provenance.iloc[-1].equals(last_row)

            # compare the parameters from the input processed stream
            # to it's output equivalent
            instream = None
            for stream in processed_streams:
                if stream[0].stats.station.lower() == 'hses':
                    instream = stream
                    break
            if instream is None:
                assert 1 == 2
            compare_streams(instream, outstream)
            workspace.close()

            # read in data from a second event and stash it in the workspace
            eventid = 'nz2018p115908'
            datafiles, origin = read_data_dir('geonet', eventid, '*.V2A')
            raw_streams = []
            for dfile in datafiles:
                raw_streams += read_data(dfile)

            event = get_event_object(origin)
            workspace = StreamWorkspace.open(tfile)
            workspace.addStreams(event, raw_streams, label='foo')

            stations = workspace.getStations(eventid)

            eventids = workspace.getEventIds()
            assert eventids == ['us1000778i', 'nz2018p115908']
            instation = raw_streams[0][0].stats.station
            this_stream = workspace.getStreams(eventid,
                                               stations=[instation],
                                               labels=['foo'])[0]
            assert instation == this_stream[0].stats.station

            # set and retrieve waveform metrics in the file
            imclist = ['greater_of_two_horizontals',
                       'channels',
                       'rotd50',
                       'rotd100']
            imtlist = ['sa1.0', 'PGA', 'pgv', 'fas2.0', 'arias']
            usid = 'us1000778i'
            tags = workspace.getStreamTags(usid)
            workspace.setStreamMetrics(eventid, labels=['foo'],
                                       imclist=imclist, imtlist=imtlist)
            summary = workspace.getStreamMetrics(eventid, instation, 'foo')
            summary_series = summary.toSeries()['ARIAS']
            cmpseries = pd.Series({'GEOMETRIC_MEAN': np.NaN,
                                   'GREATER_OF_TWO_HORIZONTALS': 0.0005,
                                   'HN1': 0.0001,
                                   'HN2': 0.0005,
                                   'HNZ': 0.0000,
                                   'ROTD100.0': 0.0005,
                                   'ROTD50.0': 0.0003})
            assert cmpseries.equals(summary_series)

            workspace.setStreamMetrics(usid, labels=['processed'])
            df = workspace.getMetricsTable(usid, labels=['processed'])
            cmpdict = {
                'GREATER_OF_TWO_HORIZONTALS': [26.904, 4.9814, 99.5713],
                'HN1': [24.5162, 4.9814, 99.5713],
                'HN2': [26.904, 4.0292, 86.7985],
                'HNZ': [16.0978, 2.5057, 156.0942]
            }
            cmpframe = pd.DataFrame(cmpdict)
            assert df['PGA'].equals(cmpframe)

            inventory = workspace.getInventory(usid)
            codes = [station.code for station in inventory.networks[0].stations]
            assert sorted(codes) == ['HSES', 'THZ', 'WPWS', 'WTMC']

    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tdir)


def test_raw():
    msg = "dataset.value has been deprecated. Use dataset[()] instead."
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=H5pyDeprecationWarning)
        warnings.filterwarnings("ignore", category=YAMLLoadWarning)
        warnings.filterwarnings("ignore", category=FutureWarning)
        raw_streams, inv = request_raw_waveforms(
            fdsn_client='IRIS',
            org_time='2018-11-30T17-29-29.330Z',
            lat=61.3464,
            lon=-149.9552,
            before_time=120,
            after_time=120,
            dist_min=0,
            dist_max=0.135,
            networks='*',
            stations='*',
            channels=['?N?'],
            access_restricted=False)
        tdir = tempfile.mkdtemp()
        try:
            edict = get_event_dict('ak20419010')
            origin = get_event_object('ak20419010')
            tfile = os.path.join(tdir, 'test.hdf')
            sc1 = StreamCollection(raw_streams)
            workspace = StreamWorkspace(tfile)
            workspace.addStreams(origin, sc1, label='raw')
            tstreams = workspace.getStreams(edict['id'])
            assert len(tstreams) == 0

            imclist = ['greater_of_two_horizontals',
                       'channels',
                       'rotd50',
                       'rotd100']
            imtlist = ['sa1.0', 'PGA', 'pgv', 'fas2.0', 'arias']
            # this shouldn't do anything
            workspace.setStreamMetrics(edict['id'],
                                       imclist=imclist, imtlist=imtlist)

            processed_streams = process_streams(sc1, edict)
            workspace.addStreams(origin, processed_streams, 'processed')
            labels = workspace.getLabels()
            tags = workspace.getStreamTags(edict['id'])
            out_raw_streams = workspace.getStreams(edict['id'], get_raw=True)
            assert len(out_raw_streams) == len(sc1)

            # this should only work on processed data
            workspace.setStreamMetrics(edict['id'],
                                       imclist=imclist, imtlist=imtlist)

            df = workspace.summarizeLabels()
            x = 1

        except Exception as e:
            raise e
        finally:
            shutil.rmtree(tdir)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_workspace()
    test_raw()
