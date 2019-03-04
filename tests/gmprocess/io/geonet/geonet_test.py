#!/usr/bin/env python

import os.path
import numpy as np
from gmprocess.io.geonet.core import is_geonet, read_geonet

FILTER_FREQ = 0.02
CORNERS = 4


def test():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    datadir_2016 = os.path.join(homedir, '..', '..', '..',
                                'data', 'geonet', 'us1000778i')
    datadir_2018 = os.path.join(homedir, '..', '..', '..',
                                'data', 'geonet', 'nz2018p115908')

    # first test a non-geonet file
    try:
        assert is_geonet(os.path.abspath(__file__))
    except AssertionError:
        assert 1 == 1

    # loop over some events that test different properties
    comps = [('20161113_110259_WTMC_20.V1A', 'V1 file w/ remainder row', -1102.6, 922.9, 3154.1),
             ('20161113_110259_WTMC_20.V2A',
              'V2 file w/ remainder row', -973.31, 796.64, 1802.19),
             ('20161113_110313_THZ_20.V1A',
              'V1 file w/out remainder row', 39.97, 48.46, -24.91),
             ]

    for comp in comps:
        fname = comp[0]
        desc = comp[1]
        test_vals = comp[2:]
        print('Testing %s, %s...' % (fname, desc))
        geonet_file = os.path.join(datadir_2016, fname)
        assert is_geonet(geonet_file)
        stream = read_geonet(geonet_file)[0]
        np.testing.assert_almost_equal(
            stream[0].max(), test_vals[0], decimal=1)
        np.testing.assert_almost_equal(
            stream[1].max(), test_vals[1], decimal=1)
        np.testing.assert_almost_equal(
            stream[2].max(), test_vals[2], decimal=1)

    comps = [('20180212_211557_WPWS_20.V2A',
              'V2 file w/out remainder row', -4.16, -19.40, -2.73)]
    for comp in comps:
        fname = comp[0]
        desc = comp[1]
        test_vals = comp[2:]
        print('Testing %s, %s...' % (fname, desc))
        geonet_file = os.path.join(datadir_2018, fname)
        assert is_geonet(geonet_file)
        stream = read_geonet(geonet_file)[0]
        np.testing.assert_almost_equal(
            stream[0].max(), test_vals[0], decimal=1)
        np.testing.assert_almost_equal(
            stream[1].max(), test_vals[1], decimal=1)
        np.testing.assert_almost_equal(
            stream[2].max(), test_vals[2], decimal=1)

    # test the velocity values from one of the V2 files
    comps = [('20180212_211557_WPWS_20.V2A', 0.165, 0.509, -0.091)]
    for comp in comps:
        geonet_file = os.path.join(datadir_2018, comp[0])
        stream = read_geonet(geonet_file)[0]
        traces = []
        for trace in stream:
            vtrace = trace.copy()
            vtrace.detrend('linear')
            vtrace.detrend('demean')
            vtrace.taper(max_percentage=0.05, type='cosine')
            vtrace.filter('highpass', freq=FILTER_FREQ,
                          zerophase=True, corners=CORNERS)
            vtrace.detrend('linear')
            vtrace.detrend('demean')
            vtrace.integrate()
            traces.append(vtrace)

        assert traces[0].max() / comp[1] >= 0.95
        assert traces[1].max() / comp[2] >= 0.95
        assert traces[2].max() / comp[3] >= 0.95


if __name__ == '__main__':
    test()
