#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from gmprocess.io.read import read_data
from gmprocess.io.test_utils import read_data_dir
from gmprocess.core.stationstream import StationStream
from gmprocess.waveform_processing.clipping.clipping_check import \
    check_clipping
from gmprocess.utils.event import get_event_object


def test_check_clipping():
    data_files, _ = read_data_dir(
        'clipping_samples', 'hv70907436', '*.mseed')
    data_files.sort()
    origin = get_event_object('hv70907436')
    streams = []
    for f in data_files:
        streams += read_data(f)

    codes = ['HV.TOUO', 'HV.MOKD', 'HV.MLOD', 'HV.HOVE', 'HV.HUAD', 'HV.HSSD']
    passed = []
    for code in codes:
        traces = []
        for ss in streams:
            tcode = "%s.%s" % (ss[0].stats.network, ss[0].stats.station)
            if tcode == code:
                traces.append(ss[0])
        st = StationStream(traces)
        check_clipping(st, origin)
        passed.append(st.passed)

    assert np.all(~np.array(passed))


if __name__ == '__main__':
    test_check_clipping()
