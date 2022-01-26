#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.waveform_processing.integrate import get_disp, get_vel
from gmprocess.utils.config import get_config


def test_get_disp():

    data_files, origin = read_data_dir("geonet", "us1000778i", "*.V1A")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    config = get_config()
    config["integration"]["frequency"] = True

    final_disp = []
    for st in sc:
        for tr in st:
            tmp_tr = get_disp(tr, config=config)
            final_disp.append(tmp_tr.data[-1])

    target_final_disp = np.array(
        [
            445.4408510389776,
            -564.5331627429107,
            95.93129050746522,
            1.4240303493834734,
            19.964467165802507,
            -0.7295398519335637,
            22.681473557944386,
            5.625360774241337,
            0.9082835404390465,
        ]
    )

    np.testing.assert_allclose(final_disp, target_final_disp, atol=1e-6)

    config["integration"]["frequency"] = False
    config["integration"]["initial"] = 0.0
    config["integration"]["demean"] = True

    final_disp = []
    for st in sc:
        for tr in st:
            tmp_tr = get_disp(tr, config=config)
            final_disp.append(tmp_tr.data[-1])

    target_final_disp = np.array(
        [
            -0.0639925584433825,
            0.06627463001467013,
            -0.023058193802552758,
            -0.0008089997861234907,
            -9.796049089918281e-05,
            -0.00020812839307250862,
            -0.0020863824158712813,
            6.607075292134614e-05,
            -7.619236969690053e-05,
        ]
    )

    np.testing.assert_allclose(final_disp, target_final_disp, atol=1e-6)


def test_get_vel():
    data_files, origin = read_data_dir("geonet", "us1000778i", "*.V1A")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    config = get_config()
    config["integration"]["frequency"] = True

    final_vel = []
    for st in sc:
        for tr in st:
            tmp_tr = get_vel(tr, config=config)
            final_vel.append(tmp_tr.data[-1])
    target_final_vel = np.array(
        [
            12.798541430544319,
            -13.254963379788103,
            4.6116344346716893,
            0.16180115030961753,
            0.019590534374707695,
            0.041625675432115872,
            0.41727678959211567,
            -0.013212254758540733,
            0.015239298475288782,
        ]
    )

    np.testing.assert_allclose(final_vel, target_final_vel, atol=1e-6)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_get_disp()
    test_get_vel()
