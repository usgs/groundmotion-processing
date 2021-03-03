#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import os.path

# third party imports
import numpy as np

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.io.test_utils import read_data_dir


def test_channels():
    datafiles, _ = read_data_dir(
        'geonet', 'us1000778i', '20161113_110259_WTMC_20.V2A')
    datafile_v2 = datafiles[0]
    stream_v2 = read_geonet(datafile_v2)[0]
    station_summary = StationSummary.from_stream(stream_v2,
                                                 ['channels'], ['pga'])
    pgms = station_summary.pgms
    np.testing.assert_almost_equal(
        pgms.loc['PGA', 'H2'].Result, 81.28979591836733, decimal=1)
    np.testing.assert_almost_equal(
        pgms.loc['PGA', 'H1'].Result, 99.3173469387755, decimal=1)
    np.testing.assert_almost_equal(
        pgms.loc['PGA', 'Z'].Result, 183.89693877551022, decimal=1)


if __name__ == '__main__':
    test_channels()
