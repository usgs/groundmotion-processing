#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.waveform_processing.integrate import get_disp, get_vel


def test_get_disp():

    data_files, origin = read_data_dir("geonet", "us1000778i", "*.V1A")
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)
    final_disp = []

    for st in sc:
        for tr in st:
            tmp_tr = get_disp(tr, method="frequency_domain")
            final_disp.append(tmp_tr.data[-1])

    target_final_disp = np.array(
        [
            1.4240303493834734,
            19.964467165802507,
            -0.7295398519335637,
            445.4408510389776,
            -564.5331627429107,
            95.93129050746522,
            22.681473557944386,
            5.625360774241337,
            0.9082835404390465,
        ]
    )

    np.testing.assert_allclose(final_disp, target_final_disp, atol=1e-6)


def test_get_vel():
    data_files, origin = read_data_dir("geonet", "us1000778i", "*.V1A")
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)
    final_vel = []

    for st in sc:
        for tr in st:
            tmp_tr = get_vel(tr, method="frequency_domain")
            final_vel.append(tmp_tr.data[-1])

    target_final_vel = np.array(
        [
            0.09343952407331428,
            0.05247204800310405,
            0.03024022273800924,
            15.375974647780472,
            -16.510746211468536,
            4.903137112699634,
            0.6851275446327221,
            -0.13432774959189756,
            -0.03563143746678422,
        ]
    )

    np.testing.assert_allclose(final_vel, target_final_vel, atol=1e-6)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_get_disp()
    test_get_vel()
