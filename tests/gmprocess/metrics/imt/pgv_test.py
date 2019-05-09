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


def test_pgv():
    datafiles, _ = read_data_dir(
        'geonet', 'us1000778i', '20161113_110259_WTMC_20.V2A')
    datafile_v2 = datafiles[0]
    stream_v2 = read_geonet(datafile_v2)[0]
    pgv_target = {}
    for trace in stream_v2:
        vtrace = trace.copy()
        vtrace.integrate()
        pgv_target[vtrace.stats['channel']] = np.abs(vtrace.max())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        station_summary = StationSummary.from_stream(stream_v2,
                                                     ['channels', 'greater_of_two_horizontals',
                                                         'gmrotd50'],
                                                     ['pgv', 'sa1.0', 'saincorrect'])
    pgv_df = station_summary.pgms[station_summary.pgms.IMT == 'PGV']
    HN1 = pgv_df[pgv_df.IMC == 'HN1'].Result.iloc[0]
    HN2 = pgv_df[pgv_df.IMC == 'HN2'].Result.iloc[0]
    HNZ = pgv_df[pgv_df.IMC == 'HNZ'].Result.iloc[0]
    np.testing.assert_almost_equal(HN2, pgv_target['HN2'])
    np.testing.assert_almost_equal(HN1, pgv_target['HN1'])
    np.testing.assert_almost_equal(HNZ, pgv_target['HNZ'])


if __name__ == '__main__':
    test_pgv()
