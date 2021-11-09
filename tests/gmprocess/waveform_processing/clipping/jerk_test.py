#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.clipping.jerk import Jerk


def test_num_outliers():
    data_files, _ = read_data_dir('clipping_samples', 'hv70907436', '*.mseed')
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    num_outliers = []
    for st in sc:
        jerk_method = Jerk(st)
        num_outliers.append(jerk_method.num_outliers)

    np.testing.assert_equal(
        num_outliers,
        np.array([1145, 1227, 872, 860, 926, 1205])
    )


def test_all_num_outliers():
    data_files, _ = read_data_dir('clipping_samples', 'hv70907436', '*.mseed')
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    num_outliers = []
    for st in sc:
        jerk_method = Jerk(st, test_all=True)
        num_outliers.append(jerk_method.num_outliers)

    np.testing.assert_equal(
        num_outliers,
        np.array([
            [1145, 1137, 1158],
            [1227, 878, 1290],
            [872, 923, 1158],
            [860, 1111, 1381],
            [926, 1025, 954],
            [1205, 1356, 1600]
        ])
    )


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_num_outliers()
    test_all_num_outliers()
