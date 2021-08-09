#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import os.path

# third party imports
import numpy as np
import pkg_resources

# local imports
from gmprocess.io.read import read_data
from gmprocess.metrics.station_summary import StationSummary


def test_sorted_duration():
    ddir = os.path.join('data', 'testdata', 'cosmos', 'us1000hyfh')
    datadir = pkg_resources.resource_filename('gmprocess', ddir)
    data_file = os.path.join(
        datadir, 'us1000hyfh_akbmrp_AKBMR--n.1000hyfh.BNZ.--.acc.V2c')
    stream = read_data(data_file)[0]

    station = StationSummary.from_stream(
        stream, ['channels'], ['sorted_duration'])
    pgms = station.pgms
    sorted_duration = pgms.loc['SORTED_DURATION', 'CHANNELS'].Result

    np.testing.assert_allclose(
        sorted_duration, 36.805, atol=1e-4, rtol=1e-4)


if __name__ == '__main__':
    test_sorted_duration()
