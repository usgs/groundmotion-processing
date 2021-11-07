#!/usr/bin/env python

import os
import numpy as np

from gmprocess.io.unam.core import is_unam, read_unam
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.io.read import read_data


def test_unam():
    datafiles, origin = read_data_dir('unam',
                                      'us2000ar20',
                                      ['CANA1709.191',
                                       'PZPU1709.191', 'ACAC1709.191'])

    # make sure format checker works
    assert is_unam(datafiles[0])

    stream = read_unam(datafiles[0])[0]
    trace1 = stream[0]
    trace2 = stream[1]
    trace3 = stream[2]

    np.testing.assert_almost_equal(
        trace1.stats.coordinates.latitude, 18.567007)
    np.testing.assert_almost_equal(
        trace1.stats.coordinates.longitude, -101.977162)
    assert trace1.stats.sampling_rate == 200.0

    np.testing.assert_almost_equal(trace1.max(), 9.14, decimal=2)
    np.testing.assert_almost_equal(trace2.max(), 9.24, decimal=2)
    np.testing.assert_almost_equal(trace3.max(), -7.87, decimal=2)

    # second file has nans for instrument period/damping...
    stream2 = read_unam(datafiles[1])[0]
    trace1 = stream2[0]
    assert np.isnan(trace1.stats.standard.instrument_period)
    assert np.isnan(trace1.stats.standard.instrument_damping)

    # third file start time is *before* the origin time
    stream3 = read_unam(datafiles[2])[0]
    trace1 = stream3[0]
    x = 1

    # make sure the reader doesn't raise exceptions on non-UNAM files
    datafiles, origin = read_data_dir('fdsn',
                                      'nc72282711',
                                      ['BK.CMB.00.HNE__20140824T102014Z__20140824T102244Z.mseed'])
    assert is_unam(datafiles[0]) is False


def test_read_past_midnight():
    # found an event near midnight, edited the start time of one
    # of the data files to test our logic that adds a day to the
    # record start time
    datafiles, origin = read_data_dir('unam',
                                      'usp000cgtd',
                                      ['CUP50401.012'])
    stream = read_unam(datafiles[0])[0]
    trace = stream[0]
    assert trace.stats.starttime > origin.time


def test_read_data():
    datafiles, origin = read_data_dir('unam',
                                      'us2000ar20',
                                      ['CANA1709.191', 'PZPU1709.191'])

    # this is a smoke test to make sure the appropriate reader is found...
    read_data(datafiles[0])


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_read_data()
    test_unam()
    test_read_past_midnight()
