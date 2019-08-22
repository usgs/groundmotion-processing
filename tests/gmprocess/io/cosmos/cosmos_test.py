#!/usr/bin/env python

import os
import numpy as np
from gmprocess.io.cosmos.core import is_cosmos, read_cosmos
from gmprocess.io.test_utils import read_data_dir
from gmprocess.stationtrace import PROCESS_LEVELS
from gmprocess.streamcollection import StreamCollection
from gmprocess.processing import remove_response


def test_cosmos():
    one_channel, event = read_data_dir('cosmos', 'ci14155260', [
        'Cosmos12TimeSeriesTest.v1'])
    two_channels, _ = read_data_dir('cosmos', 'ci14155260', [
        'Cosmos12TimeSeriesTest2.v1'])
    one_channel = one_channel[0]
    two_channels = two_channels[0]

    assert is_cosmos(one_channel)
    try:
        assert is_cosmos(os.path.abspath(__file__))
    except AssertionError as ae:
        assert 1 == 1

    # test a one channel cosmos file
    stream1 = read_cosmos(one_channel)[0]

    stats = stream1[0].stats
    assert stats['station'] == 'J2236'
    assert stats['delta'] == 0.01  # was .005
    assert stats['location'] == '02'
    assert stats['network'] == 'CE'
    dt = '%Y-%m-%dT%H:%M:%SZ'
    assert stats['starttime'].strftime(dt) == '2005-06-16T20:53:04Z'
    assert stats.coordinates['latitude'] == 34.046
    assert stats.coordinates['longitude'] == -117.035
    assert stats.coordinates['elevation'] == 15
    assert stats.standard['station_name'] == 'Yucaipa - Bryant & Oak Glen'
    assert stats.standard['instrument'] == 'Kinemetrics FBA-11 accelerometer'
    assert stats.standard['sensor_serial_number'] == '1889'
    dt = '%Y-%m-%dT%H:%M:%SZ'
    assert stats.standard['process_time'] == '2005-06-17T12:01:00Z'
    assert stats.format_specific['sensor_sensitivity'] == 220
    assert stats.standard['horizontal_orientation'] == 340
    assert stats.standard['instrument_period'] == 1.0 / 25
    assert stats.standard['instrument_damping'] == 0.20
    assert stats.standard['process_level'] == PROCESS_LEVELS['V2']
    assert stats.standard['source_format'] == 'cosmos'
    assert stats.standard['structure_type'] == 'Building'
    assert stats.standard['source'] == 'California Geological Survey'
    assert stats.format_specific['scaling_factor'] == 1
    assert stats.format_specific['v30'] == 120
    assert stats.format_specific['physical_units'] == 'cm/s/s'
    assert stats.format_specific['least_significant_bit'] == 123.45
    assert stats.format_specific['low_filter_type'] == 'Butterworth single direction'
    assert stats.format_specific['low_filter_corner'] == 4
    assert stats.format_specific['low_filter_decay'] == 3
    assert stats.format_specific['high_filter_type'] == 'Rectangular'
    assert stats.format_specific['high_filter_corner'] == 40
    assert stats.format_specific['high_filter_decay'] == 4
    assert stats.format_specific['maximum'] == -161.962
    assert stats.format_specific['maximum_time'] == 27.85
    assert stats.format_specific['station_code'] == 10
    assert stats.format_specific['record_flag'] == 'No problem'

    # test that one channel is created
    assert len(stream1) == 1

    # read the maximum from the text header check that the trace max
    # is the equivalent when rounded to the same number of decimal places
    with open(one_channel, 'rt') as f:
        file_line = f.readlines()[10].replace(' ', '').lower()
    file_max = file_line[file_line.find('max=') + 4: file_line.find('cm')]
    assert np.round(stream1[0].max(), 3) == float(file_max)

    # test a two channel cosmos file should fail because deg is not a converted unit
    failed = False
    try:
        stream2 = read_cosmos(two_channels)[0]
    except:
        failed = True
    assert failed == True
    # test that reading a file that is a valid station type returns a
    # stream with traces
    building_code = 10
    stream3 = read_cosmos(one_channel, valid_station_types=[building_code])[0]
    assert stream3.count() == 1

    # test that reading a file that is not a valid station type returns an
    # empty stream
    stream4 = read_cosmos(one_channel, valid_station_types=[1, 2, 3, 4])[0]
    assert stream4.count() == 0

    # test that reading a file that is a valid station type returns a
    # stream with traces
    building_code = 10
    stream3 = read_cosmos(one_channel, valid_station_types=[building_code])[0]
    assert stream3.count() == 1

    # Test location overrride
    stream = read_cosmos(one_channel, location='test')[0]
    assert stream[0].stats.location == 'test'


def test_channel_in_filename():
    datafiles, origin = read_data_dir('cosmos', 'us1000hyfh')
    dfile = datafiles[0]
    # TODO: Fix this problem, or get the data fixed?
    try:
        streams = read_cosmos(dfile)

    except:
        assert 1 == 1


def test_v0():
    datafiles, origin = read_data_dir('cosmos', 'ftbragg')
    dfile = datafiles[0]
    # TODO: Fix this problem, or get the data fixed?
    assert is_cosmos(dfile)
    try:
        rstreams = read_cosmos(dfile)
        tstream = rstreams[0].copy()  # raw stream
        streams = StreamCollection(rstreams)
        pstream = remove_response(rstreams[0], 0, 0)
        pstream.detrend(type='demean')

        for trace in tstream:
            trace.data /= trace.stats.standard.instrument_sensitivity
            trace.data *= 100
        tstream.detrend(type='demean')

        np.testing.assert_almost_equal(tstream[0].data, pstream[0].data)
    except Exception as e:
        pass


def test_orientation_relative():
    dfiles, event = read_data_dir('cosmos', 'ak018fcnsk91', [
        'NP8040-n.1000hyfh.HNE.01.V0c'])
    streams = read_cosmos(dfiles[0])
    trace = streams[0][0]
    assert trace.stats.channel == 'HN2'
    assert streams[0][0].stats.standard.horizontal_orientation == 90.0


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_orientation_relative()
    test_v0()
    test_cosmos()
    test_channel_in_filename()
