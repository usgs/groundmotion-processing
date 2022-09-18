#!/usr/bin/env python
# -*- coding: utf-8 -*-

# local imports
from gmprocess.io.read import read_data
from gmprocess.metrics.oscillator import get_spectral
from gmprocess.utils.test_utils import read_data_dir


def test_spectral():
    datafiles, _ = read_data_dir("geonet", "us1000778i", "20161113_110259_WTMC_20.V2A")
    acc_file = datafiles[0]
    acc = read_data(acc_file)[0]
    get_spectral(1.0, acc, 0.05)


if __name__ == "__main__":
    test_spectral()
