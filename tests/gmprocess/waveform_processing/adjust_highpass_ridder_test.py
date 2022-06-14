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
            0.03775468299082921,
            0.04476736157976949,
            0.020862973043049,
            0.015675098138080327,
            0.025395376211540546,
            0.010053650725805293,
            0.01467571627660941,
            0.01407057646742649,
            0.013659887686300661,
        ]
    )

    np.testing.assert_allclose(output_fchp, target_fchp, atol=1e-7)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_auto_fchp()
