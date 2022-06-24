#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.clipping.histogram import Histogram


def test_num_clip_intervals():
    data_files, _ = read_data_dir("clipping_samples", "hv70907436", "*.mseed")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    num_clip_intervals = []
    for st in sc:
        hist_method = Histogram(st)
        num_clip_intervals.append(hist_method.num_clip_intervals)

    np.testing.assert_equal(num_clip_intervals, np.array([0, 9, 37, 10, 16, 8]))


def test_all_num_clip_intervals():
    data_files, _ = read_data_dir("clipping_samples", "hv70907436", "*.mseed")
    data_files.sort()
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
        np.array(
            [[0, 0, 0], [0, 9, 18], [37, 31, 8], [10, 23, 0], [16, 40, 21], [0, 0, 8]]
        ),
    )


if __name__ == "__main__":
    test_num_clip_intervals()
    test_all_num_clip_intervals()
