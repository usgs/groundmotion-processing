#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import numpy as np

from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.config import get_config

from gmprocess.waveform_processing.windows import signal_split
from gmprocess.waveform_processing.windows import signal_end
from gmprocess.waveform_processing.windows import window_checks

from gmprocess.waveform_processing.processing import get_corner_frequencies
from gmprocess.waveform_processing.snr import compute_snr, snr_check


def test_corner_frequencies():
    # Default config has 'constant' corner frequency method, so the need
    # here is to force the 'snr' method.
    data_files, origin = read_data_dir("geonet", "us1000778i", "*.V1A")
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    config = get_config()

    window_conf = config["windows"]

    processed_streams = sc.copy()
    for st in processed_streams:
        if st.passed:
            # Estimate noise/signal split time
            event_time = origin.time
            event_lon = origin.longitude
            event_lat = origin.latitude
            st = signal_split(st, origin)

            # Estimate end of signal
            end_conf = window_conf["signal_end"]
            event_mag = origin.magnitude
            print(st)
            st = signal_end(
                st,
                event_time=event_time,
                event_lon=event_lon,
                event_lat=event_lat,
                event_mag=event_mag,
                **end_conf
            )
            wcheck_conf = window_conf["window_checks"]
            st = window_checks(
                st,
                min_noise_duration=wcheck_conf["min_noise_duration"],
                min_signal_duration=wcheck_conf["min_signal_duration"],
            )

    for stream in processed_streams:
        stream = compute_snr(stream)
    for stream in processed_streams:
        stream = snr_check(stream, mag=origin.magnitude)

    lp = []
    hp = []
    for stream in processed_streams:
        if not stream.passed:
            continue
        stream = get_corner_frequencies(stream, origin, method="snr")
        if stream[0].hasParameter("corner_frequencies"):
            cfdict = stream[0].getParameter("corner_frequencies")
            lp.append(cfdict["lowpass"])
            hp.append(cfdict["highpass"])
    np.testing.assert_allclose(np.sort(hp), [0.024313, 0.024378, 0.025132], atol=1e-5)

    st = processed_streams.select(station="HSES")[0]
    lps = [tr.getParameter("corner_frequencies")["lowpass"] for tr in st]
    hps = [tr.getParameter("corner_frequencies")["highpass"] for tr in st]
    np.testing.assert_allclose(np.sort(lps), [100.0, 100.0, 100.0], atol=1e-6)
    np.testing.assert_allclose(
        np.sort(hps), [0.02431315, 0.02431315, 0.02431315], atol=1e-5
    )

    lp = []
    hp = []
    for stream in processed_streams:
        if not stream.passed:
            continue
        stream = get_corner_frequencies(stream, origin, method="snr")
        if stream[0].hasParameter("corner_frequencies"):
            cfdict = stream[0].getParameter("corner_frequencies")
            lp.append(cfdict["lowpass"])
            hp.append(cfdict["highpass"])

    np.testing.assert_allclose(
        np.sort(hp), [0.02431315, 0.02437835, 0.02513194], atol=1e-5
    )

    st = processed_streams.select(station="HSES")[0]
    lps = [tr.getParameter("corner_frequencies")["lowpass"] for tr in st]
    hps = [tr.getParameter("corner_frequencies")["highpass"] for tr in st]
    np.testing.assert_allclose(np.sort(lps), [100.0, 100.0, 100.0], atol=1e-6)
    np.testing.assert_allclose(
        np.sort(hps), [0.02431315, 0.02431315, 0.02431315], atol=1e-5
    )


def test_corner_frequencies_magnitude():
    # Default config has 'constant' corner frequency method, so the need
    # here is to force the 'magnitude' method.
    data_files, origin = read_data_dir("geonet", "us1000778i", "*.V1A")
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    config = get_config()

    window_conf = config["windows"]

    processed_streams = sc.copy()
    for st in processed_streams:
        if st.passed:
            # Estimate noise/signal split time
            event_time = origin.time
            event_lon = origin.longitude
            event_lat = origin.latitude
            st = signal_split(st, origin)

            # Estimate end of signal
            end_conf = window_conf["signal_end"]
            event_mag = origin.magnitude
            print(st)
            st = signal_end(
                st,
                event_time=event_time,
                event_lon=event_lon,
                event_lat=event_lat,
                event_mag=event_mag,
                **end_conf
            )
            wcheck_conf = window_conf["window_checks"]
            st = window_checks(
                st,
                min_noise_duration=wcheck_conf["min_noise_duration"],
                min_signal_duration=wcheck_conf["min_signal_duration"],
            )

    lp = []
    hp = []
    for stream in processed_streams:
        if not stream.passed:
            continue
        stream = get_corner_frequencies(stream, origin, method="magnitude")
        if stream[0].hasParameter("corner_frequencies"):
            cfdict = stream[0].getParameter("corner_frequencies")
            lp.append(cfdict["lowpass"])
            hp.append(cfdict["highpass"])


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_corner_frequencies()
    test_corner_frequencies_magnitude()
