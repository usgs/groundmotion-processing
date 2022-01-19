#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.waveform_processing.PolynomialFit_SJB import PolynomialFit_SJB
from gmprocess.utils.config import get_config


def test_PolynomialFit_SJB():

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
                {"type": "constant", "highpass": 0.08, "lowpass": 20},
            )

        tmp_st = PolynomialFit_SJB(st, config=config)
        for tr in tmp_st:
            initial_corners = tr.getParameter("corner_frequencies")
            output_fchp.append(initial_corners["highpass"])

    target_fchp = np.array(
        [
            0.080000000006293967,
            0.087713724604807489,
            0.080000000002670851,
            0.093946426171164152,
            0.080000000003656799,
            0.080000000000033447,
            0.080000000005855859,
            0.080000000010200967,
            0.080000000000001195,
        ]
    )

    np.testing.assert_allclose(output_fchp, target_fchp, atol=1e-6)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_PolynomialFit_SJB()
