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
            -0.063992558351628759,
            0.06627463008317136,
            -0.023058193879109012,
            -0.00080899988608673645,
            -9.7960435258670486e-05,
            -0.00020812835339201197,
            -0.0020863824232897343,
            6.6070720163402541e-05,
            -7.619236524702977e-05,
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
            5.9484747445992525e-05,
            -7.4758188086221367e-05,
            -8.6512183612441618e-06,
            2.3861611533337879e-06,
            -3.1275235785888089e-06,
            -6.3198992150681477e-09,
            6.12792249055083e-07,
            3.7917109984332564e-06,
            1.6490750675366567e-06,
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
