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
            0.36988959067393229,
            -0.73299742723316885,
            0.1137765255648102,
            -0.55555187352854052,
            2.1831940048288971,
            -1.7749477126649993,
            -0.042977720010361237,
            -0.017518138494959104,
            -0.018422681637998786,
        ]
    )

    np.testing.assert_allclose(final_acc, target_final_acc, atol=1e-6)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_correct_baseline()
