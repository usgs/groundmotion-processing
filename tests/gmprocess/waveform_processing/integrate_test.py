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
            -0.07689,
            0.082552,
            -0.024509,
            -0.00047,
            -0.000257,
            -0.000152,
            -0.003425,
            0.000671,
            0.000178,
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
            -0.076882,
            0.082549,
            -0.024512,
            -0.000469,
            -0.000259,
            -0.000152,
            -0.003425,
            0.000672,
            0.000178,
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
            -2.182293e-03,
            -1.417545e-03,
            2.111492e-03,
            -9.395322e-04,
            1.662219e-03,
            -2.690978e-04,
            1.376186e-04,
            -7.358185e-05,
            1.741465e-05,
        ]
    )

    np.testing.assert_allclose(final_vel, target_final_vel, atol=1e-6)


def test_integrate_taper():
    data_files, origin = read_data_dir("geonet", "us1000778i", "*.V1A")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    config = get_config()
    config["integration"]["taper"]["taper"] = True

    final_vel = []
    for st in sc:
        for tr in st:
            tmp_tr = tr.integrate(config=config)
            final_vel.append(tmp_tr.data[-1])

    target_final_vel = np.array(
        [
            3.896186e00,
            -4.901823e00,
            -5.722080e-01,
            1.621672e-01,
            -1.654317e-01,
            -8.242356e-04,
            -1.482590e-02,
            1.504334e-01,
            1.021050e-01,
        ]
    )

    np.testing.assert_allclose(final_vel, target_final_vel, atol=1e-6)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_get_disp()
    test_get_vel()
    test_integrate_taper()
