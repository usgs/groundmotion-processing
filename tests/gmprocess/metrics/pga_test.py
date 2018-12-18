#!/usr/bin/env python

# stdlib imports
import os.path
import warnings

# third party imports
import numpy as np

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.station_summary import StationSummary


def test_pga():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    datafile_v2 = os.path.join(homedir, '..', '..', 'data', 'geonet',
                               '20161113_110259_WTMC_20.V2A')
    stream_v2 = read_geonet(datafile_v2)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        station_summary = StationSummary.from_stream(stream_v2,
                                                     ['channels', 'greater_of_two_horizontals', 'gmrotd50',
                                                      'gmrotd100', 'gmrotd0'],
                                                     ['pga', 'sa1.0', 'saincorrect'])
    station_dict = station_summary.pgms['PGA']
    greater = station_dict['GREATER_OF_TWO_HORIZONTALS']
    np.testing.assert_almost_equal(
        station_dict['HN2'], 81.28979591836733, decimal=1)
    np.testing.assert_almost_equal(
        station_dict['HN1'], 99.3173469387755, decimal=1)
    np.testing.assert_almost_equal(
        station_dict['HNZ'], 183.89693877551022, decimal=1)
    np.testing.assert_almost_equal(greater, 99.3173469387755, decimal=1)


if __name__ == '__main__':
    test_pga()
