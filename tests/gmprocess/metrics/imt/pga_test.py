#!/usr/bin/env python

# stdlib imports
import os.path
import warnings

# third party imports
import numpy as np

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.io.test_utils import read_data_dir


def test_pga():
    datafiles, _ = read_data_dir(
        'geonet', 'us1000778i', '20161113_110259_WTMC_20.V2A')
    datafile_v2 = datafiles[0]
    stream_v2 = read_geonet(datafile_v2)[0]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        station_summary = StationSummary.from_stream(stream_v2,
                                                     ['channels', 'greater_of_two_horizontals', 'gmrotd50',
                                                      'gmrotd100', 'gmrotd0'],
                                                     ['pga', 'sa1.0', 'saincorrect'])
    pga_df = station_summary.pgms[station_summary.pgms.IMT == 'PGA']
    HN1 = pga_df[pga_df.IMC == 'HN1'].Result.iloc[0]
    HN2 = pga_df[pga_df.IMC == 'HN2'].Result.iloc[0]
    HNZ = pga_df[pga_df.IMC == 'HNZ'].Result.iloc[0]
    greater = pga_df[pga_df.IMC == 'GREATER_OF_TWO_HORIZONTALS'].Result.iloc[0]
    np.testing.assert_almost_equal(
        HN2, 81.28979591836733, decimal=1)
    np.testing.assert_almost_equal(
        HN1, 99.3173469387755, decimal=1)
    np.testing.assert_almost_equal(
        HNZ, 183.89693877551022, decimal=1)
    np.testing.assert_almost_equal(greater, 99.3173469387755, decimal=1)


if __name__ == '__main__':
    test_pga()
