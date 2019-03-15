#!/usr/bin/env python

import numpy as np

from gmprocess.io.bhrc.core import is_bhrc, read_bhrc
from gmprocess.io.test_utils import read_data_dir
from gmprocess.metrics.station_summary import StationSummary


def test_bhrc():
    datafiles, origin = read_data_dir('bhrc', 'usp000jq5p')

    # make sure format checker works
    assert is_bhrc(datafiles[0])

    raw_streams = []
    for dfile in datafiles:
        raw_streams += read_bhrc(dfile)

    peaks = {'5528': 4.793910,
             '5529': 1.024440,
             '5522': 1.595120,
             '5523': 2.291470,
             '5520': 26.189800,
             '5526': 1.319720}

    for stream in raw_streams:
        summary = StationSummary.from_stream(stream)
        cmp_value = peaks[summary.station_code]
        pga = summary.pgms['PGA']['GREATER_OF_TWO_HORIZONTALS']
        np.testing.assert_almost_equal(cmp_value, pga)
    #     fmt = '%s: %.3f, %.3f'
    #     tpl = (stream[0].stats.station,
    #            stream[0].stats.coordinates['latitude'],
    #            stream[0].stats.coordinates['longitude'])
        # print(fmt % tpl)
        # print(summary.toSeries())


if __name__ == '__main__':
    test_bhrc()
