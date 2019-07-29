#!/usr/bin/env python

import os
import numpy as np

from gmprocess.io.unam.core import is_unam, read_unam
from gmprocess.io.test_utils import read_data_dir


def test_unam():
    datafiles, origin = read_data_dir('unam',
                                      'us2000ar20',
                                      ['CANA1709.191', 'PZPU1709.191'])

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

    # second file has something strange going on...
    stream2 = read_unam(datafiles[1])[0]
    trace1 = stream2[0]
    assert np.isnan(trace1.stats.standard.instrument_period)
    assert np.isnan(trace1.stats.standard.instrument_damping)

    # make sure the reader doesn't raise exceptions on non-UNAM files
    datafiles, origin = read_data_dir('fdsn',
                                      'nc72282711',
                                      ['BK.CMB.00.HNE__20140824T102014Z__20140824T102244Z.mseed'])
    assert is_unam(datafiles[0]) is False


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_unam()
