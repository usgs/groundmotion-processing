#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.waveform_processing.baseline_correction import correct_baseline
from gmprocess.utils.config import get_config


def test_correct_baseline():

    data_files, origin = read_data_dir("geonet", "us1000778i", "*.V1A")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)
    final_acc = []

    config = get_config()
    config["integration"]["frequency"] = True

    for st in sc:
        for tr in st:
            tmp_tr = correct_baseline(tr, config=config)
            final_acc.append(tmp_tr.data[-1])

    target_final_acc = np.array(
        [
            0.599829,
            0.717284,
            -1.548017,
            0.377616,
            -0.685688,
            0.112147,
            0.024594,
            0.004697,
            -0.013296,
        ]
    )

    np.testing.assert_allclose(final_acc, target_final_acc, atol=1e-6)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_correct_baseline()
