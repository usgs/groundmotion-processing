#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.waveform_processing.adjust_highpass_ridder import ridder_fchp
from gmprocess.utils.config import get_config


def test_auto_fchp():

    data_files, origin = read_data_dir("geonet", "us1000778i", "*.V1A")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)
    output_fchp = []

    config = get_config()
    config["integration"]["frequency"] = True

    for st in sc:
        for tr in st:
            tr.setParameter(
                "corner_frequencies",
                {"type": "constant", "highpass": 0.001, "lowpass": 20},
            )

        tmp_st = ridder_fchp(st, config=config)
        for tr in tmp_st:
            initial_corners = tr.getParameter("corner_frequencies")
            output_fchp.append(initial_corners["highpass"])

    target_fchp = np.array(
        [
            0.031024652910477644,
            0.040201954139573025,
            0.02339909465120076,
            0.01876642371289307,
            0.025197886682920344,
            0.009989534090901968,
            0.018280288940540717,
            0.014260823501880076,
            0.007649411827490178,
        ]
    )

    np.testing.assert_allclose(output_fchp, target_fchp, atol=1e-6)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_auto_fchp()
