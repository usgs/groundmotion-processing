#!/usr/bin/env python3

from gmprocess.io.read import read_data
from gmprocess.windows import signal_split
import pkg_resources
import os
from obspy import UTCDateTime

from gmprocess.config import get_config
from gmprocess.utils import _get_provenance

PICKER_CONFIG = get_config(picker=True)

knet_data = os.path.join('../tests/data/process')
data_path = pkg_resources.resource_filename('gmprocess', knet_data)


def test_signal_split():

    st1 = read_data(os.path.join(data_path, 'AOM0170806140843.EW'))[0]
    st2 = read_data(os.path.join(data_path, 'AOM0170806140843.NS'))[0]
    st3 = read_data(os.path.join(data_path, 'AOM0170806140843.UD'))[0]
    st = st1 + st2 + st3

    # Test the AR pick
    PICKER_CONFIG['order_of_preference'] = ['ar', 'baer', 'cwb']
    signal_split(st, method='p_arrival', picker_config=PICKER_CONFIG)

    known_arrival = UTCDateTime(2008, 6, 13, 23, 44, 17)
    for tr in st:
        picker_arrival = _get_provenance(tr, 'signal_split')[0]['split_time']
        assert abs(picker_arrival - known_arrival) < 1

    # Test the AR pick without 3 components - defaulting to Baer picker
    # reset the processing parameters...
    for trace in st:
        trace.stats.parameters = []
    st[0].stats.channel = 'ZZZ'
    signal_split(st, method='p_arrival', picker_config=PICKER_CONFIG)

    for tr in st:
        signal_split_info = _get_provenance(tr, 'signal_split')[0]
        picker_arrival = signal_split_info['split_time']
        assert abs(picker_arrival - known_arrival) < 1
        assert signal_split_info['picker_type'] == 'baer'

    # Test CWB picker
    # reset the processing parameters...
    for trace in st:
        trace.stats.parameters = []
    PICKER_CONFIG['order_of_preference'][0] = 'cwb'
    signal_split(st, method='p_arrival', picker_config=PICKER_CONFIG)
    for tr in st:
        signal_split_info = _get_provenance(tr, 'signal_split')[0]
        picker_arrival = signal_split_info['split_time']
        assert abs(picker_arrival - known_arrival) < 1
        assert signal_split_info['picker_type'] == 'cwb'

    # Test velocity split
    # reset the processing parameters...
    for trace in st:
        trace.stats.parameters = []
    signal_split(st, event_time=UTCDateTime('2008-06-13 23:43:45'),
                 event_lon=140.881, event_lat=39.030, method='velocity')
    for tr in st:
        signal_split_info = _get_provenance(tr, 'signal_split')[0]
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


if __name__ == '__main__':
    test_signal_split()
    test_signal_end()
