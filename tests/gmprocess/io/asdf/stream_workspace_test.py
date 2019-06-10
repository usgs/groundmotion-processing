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
from gmprocess.metrics.station_summary import StationSummary
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


def test_stream_params():
    eventid = 'us1000778i'
    datafiles, event = read_data_dir('geonet',
                                     eventid,
                                     '20161113_110259_WTMC_20.V1A')
    tdir = tempfile.mkdtemp()
    streams = []
    try:
        streams += read_data(datafiles[0])
        statsdict = {'name': 'Fred', 'age': 34}
        streams[0].setStreamParam('stats', statsdict)
        tfile = os.path.join(tdir, 'test.hdf')
        workspace = StreamWorkspace(tfile)
        workspace.addEvent(event)
        workspace.addStreams(event, streams, label='stats')
        outstreams = workspace.getStreams(event.id, labels=['stats'])
        cmpdict = outstreams[0].getStreamParam('stats')
        assert cmpdict == statsdict
        workspace.close()
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tdir)


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
            assert sorted(event_tags) == ['us1000778i_hses_processed',
                                          'us1000778i_hses_raw',
                                          'us1000778i_thz_processed',
                                          'us1000778i_thz_raw',
                                          'us1000778i_wtmc_processed',
                                          'us1000778i_wtmc_raw']
            outstream = workspace.getStreams(eventid,
                                             stations=['hses'],
                                             labels=['processed'])[0]

            provenance = workspace.getProvenance(eventid, labels=['processed'])
            first_row = pd.Series({'Record': 'PROCESSED.NZ.HSES.HN1',
                                   'Processing Step': 'Remove Response',
                                   'Step Attribute': 'input_units',
                                   'Attribute Value': 'counts'})

            last_row = pd.Series({'Record': 'PROCESSED.NZ.WTMC.HNZ',
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
            usid = 'us1000778i'
            inventory = workspace.getInventory(usid)
            codes = [station.code for station in inventory.networks[0].stations]
            assert sorted(codes) == ['HSES', 'THZ', 'WPWS', 'WTMC']

    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tdir)


def test_metrics2():
    eventid = 'usb000syza'
    datafiles, event = read_data_dir('knet',
                                     eventid,
                                     '*')
    datadir = os.path.split(datafiles[0])[0]
    raw_streams = StreamCollection.from_directory(datadir)
    config = get_config()
    config['metrics']['output_imts'].append('Arias')
    config['metrics']['output_imcs'].append('arithmetic_mean')
    # turn off sta/lta check and snr checks
    newconfig = drop_processing(config, ['check_sta_lta', 'compute_snr'])
    processed_streams = process_streams(raw_streams, event, config=newconfig)

    tdir = tempfile.mkdtemp()
    try:
        tfile = os.path.join(tdir, 'test.hdf')
        workspace = StreamWorkspace(tfile)
        workspace.addEvent(event)
        workspace.addStreams(event, processed_streams, label='processed')
        workspace.calcMetrics(event.id, labels=['processed'])
        etable, imc_tables1 = workspace.getTables('processed')
        etable2, imc_tables2 = workspace.getTables('processed', config=config)
        assert 'ARITHMETIC_MEAN' not in imc_tables1
        assert 'ARITHMETIC_MEAN' in imc_tables2
        assert 'ARIAS' in imc_tables2['ARITHMETIC_MEAN']
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tdir)


def test_metrics():
    eventid = 'usb000syza'
    datafiles, event = read_data_dir('knet',
                                     eventid,
                                     '*')
    datadir = os.path.split(datafiles[0])[0]
    raw_streams = StreamCollection.from_directory(datadir)
    config = get_config()
    # turn off sta/lta check and snr checks
    newconfig = drop_processing(config, ['check_sta_lta', 'compute_snr'])
    processed_streams = process_streams(raw_streams, event, config=newconfig)

    tdir = tempfile.mkdtemp()
    try:
        tfile = os.path.join(tdir, 'test.hdf')
        workspace = StreamWorkspace(tfile)
        workspace.addEvent(event)
        workspace.addStreams(event, processed_streams, label='processed')
        stream1 = processed_streams[0]
        stream2 = processed_streams[1]
        summary1 = StationSummary.from_config(stream1)
        summary2 = StationSummary.from_config(stream2)
        workspace.setStreamMetrics(event.id, 'processed', summary1)
        workspace.setStreamMetrics(event.id, 'processed', summary2)
        workspace.calcStationMetrics(event.id, labels=['processed'])
        summary1_a = workspace.getStreamMetrics(event.id,
                                                stream1[0].stats.station,
                                                'processed')
        s1_df_in = summary1.pgms.sort_values(['IMT', 'IMC'])
        s1_df_out = summary1_a.pgms.sort_values(['IMT', 'IMC'])
        array1 = s1_df_in['Result'].as_matrix()
        array2 = s1_df_out['Result'].as_matrix()
        np.testing.assert_almost_equal(array1, array2, decimal=4)

        df = workspace.getMetricsTable(event.id)
        cmp_series = {'GREATER_OF_TWO_HORIZONTALS': 0.6787,
                      'H1': 0.3869,
                      'H2': 0.6787,
                      'Z': 0.7663}
        pga_dict = df.iloc[0]['PGA'].to_dict()
        for key, value in pga_dict.items():
            value2 = cmp_series[key]
            np.testing.assert_almost_equal(value, value2, decimal=4)

        workspace.close()
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tdir)


def drop_processing(config, keys):
    newconfig = config.copy()
    newprocess = []
    for pdict in newconfig['processing']:
        found = False
        for key in keys:
            if key in pdict:
                found = True
                break
        if not found:
            newprocess.append(pdict)
    newconfig['processing'] = newprocess
    return newconfig


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_metrics2()
    test_metrics()
    test_stream_params()
    test_workspace()
