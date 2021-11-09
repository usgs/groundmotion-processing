#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.clipping.ping import Ping


def test_num_outliers():
    data_files, _ = read_data_dir('clipping_samples', 'hv70907436', '*.mseed')
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    num_outliers = []
    for st in sc:
        ping_method = Ping(st)
        num_outliers.append(ping_method.num_outliers)

    np.testing.assert_equal(
        num_outliers,
        np.array([239, 26, 0, 6, 133, 145])
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
        ping_method = Ping(st, test_all=True)
        num_outliers.append(ping_method.num_outliers)

    np.testing.assert_equal(
        num_outliers,
        np.array([
            [239, 0, 22],
            [26, 199, 30],
            [0, 0, 0],
            [6, 8, 2],
            [133, 341, 22],
            [145, 264, 29]
        ])
    )


if __name__ == '__main__':
    test_num_outliers()
    test_all_num_outliers()
