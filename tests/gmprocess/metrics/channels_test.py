#!/usr/bin/env python

# stdlib imports
import os.path

# third party imports
import numpy as np

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.station_summary import StationSummary


def test_channels():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    datafile_v2 = os.path.join(homedir, '..', '..', 'data', 'geonet', 'us1000778i',
                               '20161113_110259_WTMC_20.V2A')
    stream_v2 = read_geonet(datafile_v2)[0]
    station_summary = StationSummary.from_stream(stream_v2,
                                                 ['channels'], ['pga'])
    station_dict = station_summary.pgms['PGA']
    np.testing.assert_almost_equal(
        station_dict['HN2'], 81.28979591836733, decimal=1)
    np.testing.assert_almost_equal(
        station_dict['HN1'], 99.3173469387755, decimal=1)
    np.testing.assert_almost_equal(
        station_dict['HNZ'], 183.89693877551022, decimal=1)


if __name__ == '__main__':
    test_channels()
