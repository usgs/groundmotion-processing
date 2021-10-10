#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gmprocess.io.read import read_data
from gmprocess.waveform_processing.windows import \
    signal_split, signal_end, trim_multiple_events, cut
import pkg_resources
import os
import numpy as np
from obspy import UTCDateTime

from gmprocess.utils.config import get_config
from gmprocess.io.test_utils import read_data_dir
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.processing import remove_response
from gmprocess.utils.event import get_event_object
from gmprocess.waveform_processing.phase import create_travel_time_dataframe
from gmprocess.waveform_processing import corner_frequencies
from gmprocess.waveform_processing.filtering import \
    lowpass_filter, highpass_filter

PICKER_CONFIG = get_config(section='pickers')

knet_data = os.path.join('data', 'testdata', 'process')
data_path = pkg_resources.resource_filename('gmprocess', knet_data)


def _test_signal_split():

    st1 = read_data(os.path.join(data_path, 'AOM0170806140843.EW'))[0]
    st2 = read_data(os.path.join(data_path, 'AOM0170806140843.NS'))[0]
    st3 = read_data(os.path.join(data_path, 'AOM0170806140843.UD'))[0]
    st = st1 + st2 + st3

    # Test the AR pick
    PICKER_CONFIG['order_of_preference'] = ['ar', 'baer', 'cwb']
    signal_split(st, method='p_arrival', picker_config=PICKER_CONFIG)

    known_arrival = UTCDateTime(2008, 6, 13, 23, 44, 17)
    for tr in st:
        picker_arrival = tr.getParameter('signal_split')['split_time']
        assert abs(picker_arrival - known_arrival) < 1

    # Test the AR pick without 3 components - defaulting to Baer picker
    # reset the processing parameters...
    for trace in st:
        trace.stats.parameters = []
    st[0].stats.channel = '--'
    signal_split(st, method='p_arrival', picker_config=PICKER_CONFIG)

    for tr in st:
        signal_split_info = tr.getParameter('signal_split')
        picker_arrival = signal_split_info['split_time']
        assert abs(picker_arrival - known_arrival) < 1
        assert signal_split_info['picker_type'] == 'baer'

    # Test CWB picker
    # reset the processing parameters...

    # TODO - uncomment this and fix!!
    # for trace in st:
    #     trace.stats.parameters = []
    # PICKER_CONFIG['order_of_preference'][0] = 'cwb'
    # signal_split(st, method='p_arrival', picker_config=PICKER_CONFIG)
    # for tr in st:
    #     signal_split_info = tr.getParameter('signal_split')
    #     picker_arrival = signal_split_info['split_time']
    #     assert abs(picker_arrival - known_arrival) < 1
    #     assert signal_split_info['picker_type'] == 'cwb'

    # Test velocity split
    # reset the processing parameters...
    for trace in st:
        trace.stats.parameters = []
    signal_split(st, event_time=UTCDateTime('2008-06-13 23:43:45'),
                 event_lon=140.881, event_lat=39.030, method='velocity')
    for tr in st:
        signal_split_info = tr.getParameter('signal_split')
        assert signal_split_info['method'] == 'velocity'
        assert signal_split_info['picker_type'] is None

    # Test an invalid picker type
    PICKER_CONFIG['order_of_preference'][0] = 'invalid'
    success = False
    try:
        signal_split(st, method='p_arrival', picker_config=PICKER_CONFIG)
        success = True
    except ValueError:
        pass
    assert success is False

    # Test an invalid split method
    success = False
    try:
        signal_split(st, method='invalid')
        success = True
    except ValueError:
        pass
    assert success is False


def test_signal_end():
    pass


def test_signal_split2():
    datafiles, origin = read_data_dir(
        'knet', 'us2000cnnl', 'AOM0011801241951*')
    streams = []
    for datafile in datafiles:
        streams += read_data(datafile)

    streams = StreamCollection(streams)
    stream = streams[0]
    signal_split(stream, origin)

    cmpdict = {
        'split_time': UTCDateTime(2018, 1, 24, 10, 51, 39, 841483),
        'method': 'p_arrival',
        'picker_type': 'travel_time'}

    pdict = stream[0].getParameter('signal_split')
    for key, value in cmpdict.items():
        v1 = pdict[key]
        # because I can't figure out how to get utcdattime __eq__
        # operator to behave as expected with the currently installed
        # version of obspy, we're going to pedantically compare two
        # of these objects...
        if isinstance(value, UTCDateTime):
            # value.__precision = 4
            # v1.__precision = 4
            assert value.year == v1.year
            assert value.month == v1.month
            assert value.day == v1.day
            assert value.hour == v1.hour
            assert value.minute == v1.minute
            assert value.second == v1.second
        else:
            assert v1 == value


def test_trim_multiple_events():
    datapath = os.path.join('data', 'testdata', 'multiple_events')
    datadir = pkg_resources.resource_filename('gmprocess', datapath)
    sc = StreamCollection.from_directory(
        os.path.join(datadir, 'ci38457511'))
    origin = get_event_object('ci38457511')
    df, catalog = create_travel_time_dataframe(
        sc, os.path.join(datadir, 'catalog.csv'), 5, 0.1, 'iasp91')
    for st in sc:
        st.detrend('demean')
        remove_response(st, None, None)
        st = corner_frequencies.get_constant(st)
        lowpass_filter(st)
        highpass_filter(st)
        signal_split(st, origin)
        signal_end(st, origin.time, origin.longitude, origin.latitude,
                   origin.magnitude, method='model', model='AS16')
        cut(st, 2)
        trim_multiple_events(st, origin, catalog, df, 0.2, 0.7, 'B14',
                             {'vs30': 760}, {'rake': 0})

    num_failures = sum([1 if not st.passed else 0 for st in sc])
    assert num_failures == 2

    failure = sc.select(station='WRV2')[0][0].getParameter('failure')
    assert failure['module'] == 'trim_multiple_events'
    assert failure['reason'] == ('A significant arrival from another event '
                                 'occurs within the first 70.0 percent of the '
                                 'signal window')

    for tr in sc.select(station='JRC2')[0]:
        np.testing.assert_almost_equal(
            tr.stats.endtime,
            UTCDateTime('2019-07-06T03:20:56.368300Z'))


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_signal_split2()
    test_signal_end()
    test_trim_multiple_events()
