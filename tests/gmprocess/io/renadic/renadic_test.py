#!/usr/bin/env python

import os
import numpy as np

from gmprocess.io.renadic.core import is_renadic, read_renadic
from gmprocess.utils.test_utils import read_data_dir


def test_renadic():
    datafiles, origin = read_data_dir('renadic',
                                      'official20100227063411530_30')

    # make sure format checker works
    assert is_renadic(datafiles[0])

    raw_streams = []
    for dfile in datafiles:
        print('Reading file %s...' % dfile)
        raw_streams += read_renadic(dfile)

    # following pga values in G taken from file headers
    peaks = {'672': (-0.030, -0.016, -0.008),
             '5014': (0.295, -0.155, 0.421),
             '0': (0.020, -0.019, -0.010)}

    for stream in raw_streams:
        if stream[0].stats.station not in peaks:
            continue
        cmp_value = np.abs(np.array(peaks[stream[0].stats.station]))
        pga1 = np.abs(stream[0].max())
        pga2 = np.abs(stream[1].max())
        pga3 = np.abs(stream[2].max())
        tpl = np.array((pga1, pga2, pga3)) / 980
        np.testing.assert_almost_equal(cmp_value, tpl, decimal=3)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_renadic()
