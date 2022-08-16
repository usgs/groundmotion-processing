#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import numpy as np
from obspy import UTCDateTime

from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.config import get_config, update_dict
from gmprocess.utils.event import get_event_object
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.utils.constants import TEST_DATA_DIR


def test_lowpass_max():
    datadir = TEST_DATA_DIR / "lowpass_max"
    sc = StreamCollection.from_directory(datadir)
    sc.describe()

    conf = get_config()
    update = {
        "processing": [
            {"detrend": {"detrending_method": "demean"}},
            {
                "remove_response": {
                    "pre_filt": True,
                    "f1": 0.001,
                    "f2": 0.005,
                    "f3": None,
                    "f4": None,
                    "water_level": 60,
                }
            },
            {
                "get_corner_frequencies": {
                    "constant": {"highpass": 0.08, "lowpass": 20.0},
                    "method": "constant",
                    "snr": {"same_horiz": True},
                }
            },
            {"lowpass_max_frequency": {"fn_fac": 0.9}},
        ]
    }
    update_dict(conf, update)
    update = {
        "windows": {
            "signal_end": {
                "method": "model",
                "vmin": 1.0,
                "floor": 120,
                "model": "AS16",
                "epsilon": 2.0,
            },
            "window_checks": {
                "enabled": False,
                "min_noise_duration": 1.0,
                "min_signal_duration": 1.0,
            },
        }
    }
    update_dict(conf, update)
    edict = {
        "id": "ci38038071",
        "time": UTCDateTime("2018-08-30 02:35:36"),
        "lat": 34.136,
        "lon": -117.775,
        "depth": 5.5,
        "magnitude": 4.4,
    }
    event = get_event_object(edict)
    test = process_streams(sc, event, conf)
    for st in test:
        for tr in st:
            freq_dict = tr.getParameter("corner_frequencies")
            np.testing.assert_allclose(freq_dict["lowpass"], 18.0)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_lowpass_max()
