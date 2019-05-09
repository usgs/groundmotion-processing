#!/usr/bin/env python

# stdlib imports
import os.path

# third party imports
import numpy as np

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.io.test_utils import read_data_dir


def test_greater_of_two_horizontals():
    datafiles, _ = read_data_dir(
        'geonet', 'us1000778i', '20161113_110259_WTMC_20.V2A')
    datafile_v2 = datafiles[0]
    stream_v2 = read_geonet(datafile_v2)[0]
    station_summary = StationSummary.from_stream(stream_v2,
                                                 ['greater_of_two_horizontals'], ['pga'])
    station = station_summary.pgms[station_summary.pgms.IMT == 'PGA']
    greater = station[station.IMC == 'GREATER_OF_TWO_HORIZONTALS'].Result.iloc[0]
    np.testing.assert_almost_equal(greater, 99.3173469387755, decimal=1)


if __name__ == '__main__':
    test_greater_of_two_horizontals()
