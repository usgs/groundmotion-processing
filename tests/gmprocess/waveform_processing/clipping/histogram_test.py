#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from gmprocess.io.read import read_data
from gmprocess.io.test_utils import read_data_dir
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.clipping.histogram import Histogram


def test_num_clip_intervals():
    data_files, _ = read_data_dir('clipping_samples', 'hv70907436', '*.mseed')
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    num_clip_intervals = []
    for st in sc:
        hist_method = Histogram(st)
        num_clip_intervals.append(hist_method.num_clip_intervals)

    np.testing.assert_equal(
        num_clip_intervals,
        np.array([23, 7, 9, 0, 17, 37])
    )


def test_all_num_clip_intervals():
    data_files, _ = read_data_dir('clipping_samples', 'hv70907436', '*.mseed')
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    num_clip_intervals = []
    for st in sc:
        hist_method = Histogram(st, test_all=True)
        num_clip_intervals.append(hist_method.num_clip_intervals)

    np.testing.assert_equal(
        num_clip_intervals,
        np.array([[23, 0, 10],
                  [7, 0, 0],
                  [9, 17, 0],
                  [0, 0, 0],
                  [17, 37, 20],
                  [37, 31, 8]])
    )


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_num_clip_intervals()
    test_all_num_clip_intervals()
