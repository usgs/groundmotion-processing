#!/usr/bin/env python

# stdlib imports
import os.path

# third party imports
import numpy as np

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.station_summary import StationSummary


def test_greater_of_two_horizontals():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    datafile_v2 = os.path.join(homedir, '..', '..', 'data', 'geonet',
                               '20161113_110259_WTMC_20.V2A')
    stream_v2 = read_geonet(datafile_v2)
    station_summary = StationSummary.from_stream(stream_v2,
                                                 ['greater_of_two_horizontals'], ['pga'])
    station_dict = station_summary.pgms['PGA']
    greater = station_dict['GREATER_OF_TWO_HORIZONTALS']
    np.testing.assert_almost_equal(greater, 99.3173469387755, decimal=1)


if __name__ == '__main__':
    test_greater_of_two_horizontals()
