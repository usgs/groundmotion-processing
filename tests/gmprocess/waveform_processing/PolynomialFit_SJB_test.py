#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.waveform_processing.PolynomialFit_SJB import PolynomialFit_SJB


def test_PolynomialFit_SJB():

    data_files, origin = read_data_dir("geonet", "us1000778i", "*.V1A")
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)
    output_fchp = []

    for st in sc:
        tmp_st = PolynomialFit_SJB(st)
        for tr in tmp_st:
            initial_corners = tr.getParameter("corner_frequencies")
            output_fchp.append(initial_corners["highpass"])

    target_fchp = np.array(
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

    np.testing.assert_allclose(output_fchp, target_fchp, atol=1e-6)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_correct_baseline()
