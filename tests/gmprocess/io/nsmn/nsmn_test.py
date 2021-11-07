#!/usr/bin/env python

import os
import numpy as np

from gmprocess.io.nsmn.core import is_nsmn, read_nsmn
from gmprocess.utils.test_utils import read_data_dir


def test_nsmn():
    datafiles, origin = read_data_dir('nsmn', 'us20009ynd')

    # make sure format checker works
    assert is_nsmn(datafiles[0])

    raw_streams = []
    for dfile in datafiles:
        raw_streams += read_nsmn(dfile)

    peaks = {'0921': (13.200332, 12.163827, 9.840572),
             '4304': (1.218825, 1.207812, 0.645862),
             '5405': (1.023915, 1.107856, 0.385138)}

    coords = {'0921': (37.87470, 27.59223),
              '4304': (38.99478, 29.40040),
              '5405': (40.79609, 30.73520)}

    for stream in raw_streams:
        cmp_value = peaks[stream[0].stats.station]
        pga1 = np.abs(stream[0].max())
        pga2 = np.abs(stream[1].max())
        pga3 = np.abs(stream[2].max())
        tpl = (pga1, pga2, pga3)
        np.testing.assert_almost_equal(cmp_value, tpl)
        cmp_coords = coords[stream[0].stats.station]
        tpl = (stream[0].stats['coordinates']['latitude'],
               stream[0].stats['coordinates']['longitude'])
        np.testing.assert_almost_equal(cmp_coords, tpl)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_nsmn()
