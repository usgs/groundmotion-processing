#!/usr/bin/env python
# stdlib imports
import os

# third party imports
import numpy as np

# local imports
from gmprocess.constants import GAL_TO_PCTG
from gmprocess.io.read import read_data
from gmprocess.metrics.oscillators import get_acceleration, get_spectral, get_velocity
from gmprocess.io.test_utils import read_data_dir


def test_acceleration():
    datafiles, _ = read_data_dir(
        'geonet', 'us1000778i', '20161113_110259_WTMC_20.V2A')
    acc_file = datafiles[0]
    acc = read_data(acc_file)[0]
    target_g = acc[0].data * GAL_TO_PCTG
    target_m = acc[0].data / 100
    target_cm = acc[0].data

    acc_g = get_acceleration(acc, units='%%g')
    assert acc_g[0].stats['units'] == '%%g'
    np.testing.assert_allclose(acc_g[0], target_g)

    acc_m = get_acceleration(acc, units='m/s/s')
    assert acc_m[0].stats['units'] == 'm/s/s'
    np.testing.assert_allclose(acc_m[0], target_m)

    acc_cm = get_acceleration(acc, units='cm/s/s')
    assert acc_cm[0].stats['units'] == 'cm/s/s'
    np.testing.assert_allclose(acc_cm[0], target_cm)


def test_spectral():
    datafiles, _ = read_data_dir(
        'geonet', 'us1000778i', '20161113_110259_WTMC_20.V2A')
    acc_file = datafiles[0]
    acc = read_data(acc_file)[0]
    get_spectral(1.0, acc, 0.05)


def test_velocity():
    datafiles, _ = read_data_dir(
        'geonet', 'us1000778i', '20161113_110259_WTMC_20.V2A')
    acc_file = datafiles[0]
    acc = read_data(acc_file)[0]
    target_v = acc.copy().integrate()[0]
    v = get_velocity(acc)
    np.testing.assert_allclose(v[0], target_v)


if __name__ == '__main__':
    test_acceleration()
    test_spectral()
    test_velocity()
