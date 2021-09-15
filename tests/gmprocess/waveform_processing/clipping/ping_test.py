#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from gmprocess.io.read import read_data
from gmprocess.io.test_utils import read_data_dir
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.clipping.ping import Ping


def test_num_outliers():
    data_files, _ = read_data_dir('clipping_samples', 'hv70907436', '*.mseed')
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
        np.array([8, 29, 199, 239, 133, 0])
    )


def test_all_num_outliers():
    data_files, _ = read_data_dir('clipping_samples', 'hv70907436', '*.mseed')
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
        np.array([[8, 2, 6],
                  [29, 264, 145],
                  [199, 30, 26],
                  [239, 22, 0],
                  [133, 341, 22],
                  [0, 0, 0]])
    )


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_num_outliers()
    test_all_num_outliers()