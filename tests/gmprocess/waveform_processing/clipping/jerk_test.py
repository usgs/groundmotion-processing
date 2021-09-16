#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from gmprocess.io.read import read_data
from gmprocess.io.test_utils import read_data_dir
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
        np.array([1137, 878, 923, 1111, 1025, 1356])
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
            [0, 1137, 1060],
            [0, 878, 1298],
            [0, 923, 806],
            [0, 1111, 1277],
            [0, 1025, 1071],
            [0, 1356, 1542]
        ])
    )


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_num_outliers()
    test_all_num_outliers()
