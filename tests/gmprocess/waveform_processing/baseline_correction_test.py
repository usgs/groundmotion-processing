#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.waveform_processing.baseline_correction import correct_baseline


def test_correct_baseline():

    data_files, origin = read_data_dir("geonet", "us1000778i", "*.V1A")
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)
    final_acc = []

    for st in sc:
        for tr in st:
            tmp_tr = correct_baseline(tr)
            final_acc.append(tmp_tr.data[-1])

    target_final_acc = np.array(
        [
            0.38171449098966037,
            -0.68116345356671115,
            0.1141872852255339,
            1.2431553228809777,
            0.063481378706976788,
            -1.2831541242023428,
            0.051703963263167764,
            -0.0017171449230287891,
            -0.015051772443350092,
        ]
    )

    np.testing.assert_allclose(final_acc, target_final_acc, atol=1e-6)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_correct_baseline()
