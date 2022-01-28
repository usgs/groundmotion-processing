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
            0.56461289786733748,
            0.7635810301596887,
            -1.5336827747344823,
            0.37347216612067624,
            -0.68279908493209274,
            0.11194271460518387,
            0.026918464474989107,
            -0.0001845868080251542,
            -0.015623699510497829,
        ]
    )

    np.testing.assert_allclose(final_acc, target_final_acc, atol=1e-6)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_correct_baseline()
