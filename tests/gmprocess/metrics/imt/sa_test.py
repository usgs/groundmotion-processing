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


def test_sa():
    datafiles, _ = read_data_dir(
        'geonet', 'us1000778i', '20161113_110259_WTMC_20.V2A')
    datafile_v2 = datafiles[0]
    stream_v2 = read_geonet(datafile_v2)[0]
    sa_target = {}
    for trace in stream_v2:
        vtrace = trace.copy()
        vtrace.integrate()
        sa_target[vtrace.stats['channel']] = np.abs(vtrace.max())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        station_summary = StationSummary.from_stream(stream_v2,
                                                     ['greater_of_two_horizontals',
                                                      'gmrotd50', 'channels'],
                                                     ['sa1.0', 'saincorrect'])
    pgms = station_summary.pgms
    assert 'SA(1.0)' in pgms.IMT.tolist()


if __name__ == '__main__':
    test_sa()
