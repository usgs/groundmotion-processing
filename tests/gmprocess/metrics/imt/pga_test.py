#!/usr/bin/env python

# stdlib imports
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
        station_summary = StationSummary.from_stream(
            stream_v2,
            ['channels', 'greater_of_two_horizontals', 'gmrotd50',
             'gmrotd100', 'gmrotd0', 'rotd50', 'geometric_mean',
             'arithmetic_mean'],
            ['pga', 'sa1.0', 'saincorrect'])
    pga_df = station_summary.pgms[station_summary.pgms.IMT == 'PGA']
    AM = pga_df[pga_df.IMC == 'ARITHMETIC_MEAN'].Result.iloc[0]
    GM = pga_df[pga_df.IMC == 'GEOMETRIC_MEAN'].Result.iloc[0]
    HN1 = pga_df[pga_df.IMC == 'H1'].Result.iloc[0]
    HN2 = pga_df[pga_df.IMC == 'H2'].Result.iloc[0]
    HNZ = pga_df[pga_df.IMC == 'Z'].Result.iloc[0]
    greater = pga_df[pga_df.IMC == 'GREATER_OF_TWO_HORIZONTALS'].Result.iloc[0]
    np.testing.assert_allclose(
        AM, 90.242335558014219, rtol=1e-3)
    np.testing.assert_allclose(
        GM, 89.791654017670112, rtol=1e-3)
    np.testing.assert_allclose(
        HN2, 81.234672390673683, rtol=1e-3)
    np.testing.assert_allclose(
        HN1, 99.249998725354743, rtol=1e-3)
    np.testing.assert_almost_equal(
        HNZ, 183.77223618666929, decimal=1)
    np.testing.assert_allclose(
        greater, 99.249998725354743, rtol=1e-3)


if __name__ == '__main__':
    test_pga()
