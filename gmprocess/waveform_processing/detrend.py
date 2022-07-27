#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from gmprocess.waveform_processing.processing_step import ProcessingStep
from gmprocess.waveform_processing.baseline_correction import correct_baseline


@ProcessingStep
def detrend(st, detrending_method=None, config=None):
    """
    Detrend stream.

    Args:
        st (StationStream):
            Stream of data.
        method (str):
            Method to detrend; valid options include the 'type' options supported by
            obspy.core.trace.Trace.detrend as well as:
                - 'baseline_sixth_order', which is for a baseline correction
                   method that fits a sixth-order polynomial to the
                   displacement time series, and sets the zeroth- and
                   first-order terms to be zero. The second derivative of the
                   fit polynomial is then removed from the acceleration time
                   series.
                - 'pre', for removing the mean of the pre-event noise window.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Detrended stream.
    """

    if not st.passed:
        return st

    for tr in st:
        if detrending_method == "baseline_sixth_order":
            tr = correct_baseline(tr, config)
        elif detrending_method == "pre":
            tr = _detrend_pre_event_mean(tr, config)
        else:
            tr = tr.detrend(detrending_method)

        tr.setProvenance("detrend", {"detrending_method": detrending_method})

    return st


def _detrend_pre_event_mean(trace, config=None):
    """
    Subtraces the mean of the pre-event noise window from the full trace.

    Args:
        trace (obspy.core.trace.Trace):
            Trace of strong motion data.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        trace: Detrended trace.
    """
    split_prov = trace.getParameter("signal_split")
    if isinstance(split_prov, list):
        split_prov = split_prov[0]
    split_time = split_prov["split_time"]
    noise = trace.copy().trim(endtime=split_time)
    noise_mean = np.mean(noise.data)
    trace.data = trace.data - noise_mean
    return trace
