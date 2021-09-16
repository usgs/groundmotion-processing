#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from gmprocess.io.read import read_data
from gmprocess.io.test_utils import read_data_dir
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.clipping.std_dev import Std_Dev


def test_num_outliers():
    data_files, _ = read_data_dir('clipping_samples', 'hv70907436', '*.mseed')
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    num_outliers = []
    for st in sc:
        std_dev_method = Std_Dev(st)
        num_outliers.append(std_dev_method.num_outliers)

    np.testing.assert_equal(
        num_outliers,
        np.array([76, 4862, 1086, 0, 60, 131])
    )


def test_all_num_outliers():
    data_files, _ = read_data_dir('clipping_samples', 'hv70907436', '*.mseed')
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    num_outliers = []
    for st in sc:
        std_dev_method = Std_Dev(st, test_all=True)
        num_outliers.append(std_dev_method.num_outliers)

    np.testing.assert_equal(
        num_outliers,
        np.array([[76, 0, 1018],
                  [4862, 0, 0],
                  [1086, 23, 0],
                  [0, 0, 0],
                  [60, 1314, 1511],
                  [131, 252, 4482]])
    )


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_num_outliers()
    test_all_num_outliers()
