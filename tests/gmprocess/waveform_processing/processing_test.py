#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

import numpy as np

from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.utils.logging import setup_logger
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.config import update_config, get_config
from gmprocess.utils.constants import TEST_DATA_DIR

CONFIG = get_config()

setup_logger()


def test_process_streams():
    # Loma Prieta test station (nc216859)

    data_files, origin = read_data_dir("geonet", "us1000778i", "*.V1A")
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    sc.describe()

    config = update_config(TEST_DATA_DIR / "config_min_freq_0p2.yml", CONFIG)

    test = process_streams(sc, origin, config=config)

    logging.info(f"Testing trace: {test[0][1]}")

    assert len(test) == 3
    assert len(test[0]) == 3
    assert len(test[1]) == 3
    assert len(test[2]) == 3

    # Apparently the traces end up in a different order on the Travis linux
    # container than on my local mac. So testing individual traces need to
    # not care about trace order.

    trace_maxes = np.sort(
        [np.max(np.abs(t.data)) for t in test.select(station="HSES")[0]]
    )

    np.testing.assert_allclose(
        trace_maxes, np.array([157.812449, 240.379521, 263.601519]), rtol=1e-5
    )


def test_free_field():
    data_files, origin = read_data_dir("kiknet", "usp000hzq8")
    raw_streams = []
    for dfile in data_files:
        raw_streams += read_data(dfile)

    sc = StreamCollection(raw_streams)

    processed_streams = process_streams(sc, origin)

    # all of these streams should have failed for different reasons
    npassed = np.sum([pstream.passed for pstream in processed_streams])
    assert npassed == 0
    for pstream in processed_streams:
        is_free = pstream[0].free_field
        reason = ""
        for trace in pstream:
            if not trace.passed:
                reason = trace.getParameter("failure")["reason"]
                break
        if is_free:
            assert reason.startswith("Failed")
        else:
            assert reason == "Failed free field sensor check."


def test_check_instrument():
    data_files, origin = read_data_dir("fdsn", "nc51194936", "*.mseed")
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)
    sc.describe()

    config = update_config(TEST_DATA_DIR / "config_test_check_instr.yml", CONFIG)
    test = process_streams(sc, origin, config=config)

    for sta, expected in [("CVS", True), ("GASB", True), ("SBT", False)]:
        st = test.select(station=sta)[0]
        logging.info(f"Testing stream: {st}")
        assert st.passed == expected


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_process_streams()
    test_free_field()
