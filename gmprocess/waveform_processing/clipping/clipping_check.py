#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from obspy.geodetics.base import gps2dist_azimuth

from gmprocess.waveform_processing.clipping.clipping_ann import clipNet
from gmprocess.waveform_processing.clipping.max_amp import Max_Amp
from gmprocess.waveform_processing.clipping.histogram import Histogram
from gmprocess.waveform_processing.clipping.ping import Ping
from gmprocess.waveform_processing.processing_step import ProcessingStep

M_TO_KM = 1.0 / 1000


@ProcessingStep
def check_clipping(st, origin, threshold=0.2, config=None):
    """Apply clicking check.

    Lower thresholds will pass fewer streams but will give less false negatives
    (i.e., streams in which clipping actually occurred but were missed).

    Args:
        st (StationStream):
           Trace of data.
        origin (ScalarEvent):
            ScalarEvent object.
        threshold (float):
            Threshold probability.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream checked for clipping.

    """
    # Don't bother with test for strong motion instruments
    chan_code = st[0].stats.channel
    if chan_code[1] == "N":
        return st

    # Don't bother with test if it has already failed
    if not st.passed:
        return st

    event_mag = origin.magnitude
    event_lon = origin.longitude
    event_lat = origin.latitude
    dist = (
        gps2dist_azimuth(
            lat1=event_lat,
            lon1=event_lon,
            lat2=st[0].stats["coordinates"]["latitude"],
            lon2=st[0].stats["coordinates"]["longitude"],
        )[0]
        * M_TO_KM
    )

    # Clip mag/dist to range of training dataset
    event_mag = np.clip(event_mag, 4.0, 8.8)
    dist = np.clip(dist, 0.0, 445.0)

    clip_nnet = clipNet()

    max_amp_method = Max_Amp(st, max_amp_thresh=6e6)
    hist_method = Histogram(st)
    ping_method = Ping(st)
    inputs = [
        event_mag,
        dist,
        max_amp_method.is_clipped,
        hist_method.is_clipped,
        ping_method.is_clipped,
    ]
    prob_clip = clip_nnet.evaluate(inputs)[0][0]

    if prob_clip >= threshold:
        for tr in st:
            tr.fail(f"Failed clipping check: prob_clip = {prob_clip:.2f}.")

    return st
