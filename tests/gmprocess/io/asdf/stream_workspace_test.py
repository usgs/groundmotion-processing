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

from h5py.h5py_warnings import H5pyDeprecationWarning
from yaml import YAMLLoadWarning
from obspy.core.utcdatetime import UTCDateTime

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
    datafiles, event = read_data_dir('geonet', eventid, '*.V1A')
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
            processed_streams = process_streams(sc, event, config=config)
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
                                  'Processing Step': 'Lowpass Filter',
                                  'Step Attribute': 'number_of_passes',
                                  'Attribute Value': 2})
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
            datafiles, event = read_data_dir('geonet', eventid, '*.V2A')
            raw_streams = []
            for dfile in datafiles:
                raw_streams += read_data(dfile)

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
                       'rotd100', 'arithmetic_mean']
            imtlist = ['sa1.0', 'PGA', 'pgv', 'fas2.0', 'arias']
            usid = 'us1000778i'
            tags = workspace.getStreamTags(usid)
            workspace.setStreamMetrics(eventid, labels=['foo'],
                                       imclist=imclist, imtlist=imtlist)
            summary = workspace.getStreamMetrics(eventid, instation, 'foo')
            summary_series = summary.toSeries()['ARIAS']
            cmpseries = pd.Series({'ARITHMETIC_MEAN': 0.0001,
                                   'GREATER_OF_TWO_HORIZONTALS':np.NaN,
                                   'HN1': np.NaN,
                                   'HN2': np.NaN,
                                   'HNZ': np.NaN,
                                   'ROTD100.0': np.NaN,
                                   'ROTD50.0': np.NaN})
            assert cmpseries.equals(summary_series)

            workspace.setStreamMetrics(usid, labels=['processed'])
            df = workspace.getMetricsTable(usid, labels=['processed'])

            data = np.array([[26.8877, 24.5076, 26.8877, 16.0931],
                             [4.9814, 4.9814, 4.0292, 2.5057],
                             [99.6077, 99.6077, 86.7887, 151.8803]])
            cmpdict = pd.DataFrame(data,
                                   columns=['GREATER_OF_TWO_HORIZONTALS', 'HN1', 'HN2', 'HNZ'])

            cmpframe = pd.DataFrame(cmpdict)
            assert df['PGA'].equals(cmpframe)

            inventory = workspace.getInventory(usid)
            codes = [station.code for station in inventory.networks[0].stations]
            assert sorted(codes) == ['HSES', 'THZ', 'WPWS', 'WTMC']

    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tdir)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_workspace()
