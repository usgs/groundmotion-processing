#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging


def highpass_filter(
    st, frequency_domain=True, filter_order=5, number_of_passes=2, config=None
):
    """
    Highpass filter.

    Args:
        st (StationStream):
            Stream of data.
        frequency_domain (Bool):
            If true, use gmprocess frequency domain implementation; "
            " if false, use ObsPy filters."
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Filtered streams.
    """
    if not st.passed:
        return st

    for tr in st:
        tr = highpass_filter_trace(tr, filter_order, number_of_passes, config)

    return st


def highpass_filter_trace(tr, filter_order=5, number_of_passes=2, config=None):
    """
    Highpass filter.

    Args:
        tr (StationTrace):
            Stream of data.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.

    Returns:
        StationTrace: Filtered trace.
    """
    if number_of_passes == 1:
        zerophase = False
    elif number_of_passes == 2:
        zerophase = True
    else:
        raise ValueError("number_of_passes must be 1 or 2.")
    try:
        freq_dict = tr.getParameter("corner_frequencies")
        freq = freq_dict["highpass"]

        tr.filter(
            type="highpass",
            config=config,
            freq=freq,
            corners=filter_order,
            zerophase=zerophase,
        )

    except BaseException as e:
        tr.fail(f"Highpass filter failed with excpetion: {e}")
    return tr


def lowpass_filter(st, filter_order=5, number_of_passes=2, config=None):
    """
    Lowpass filter.

    Args:
        st (StationStream):
            Stream of data.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Filtered streams.
    """
    if not st.passed:
        return st

    for tr in st:
        tr = lowpass_filter_trace(tr, filter_order, number_of_passes)

    return st


def lowpass_filter_trace(tr, filter_order=5, number_of_passes=2):
    """
    Lowpass filter.

    Args:
        tr (StationTrace):
            Stream of data.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.

    Returns:
        StationTrace: Filtered trace.
    """
    if number_of_passes == 1:
        zerophase = False
    elif number_of_passes == 2:
        zerophase = True
    else:
        raise ValueError("number_of_passes must be 1 or 2.")

    freq_dict = tr.getParameter("corner_frequencies")
    freq = freq_dict["lowpass"]
    try:
        tr.filter(type="lowpass", freq=freq, corners=filter_order, zerophase=zerophase)
        tr.setProvenance(
            "lowpass_filter",
            {
                "filter_type": "Butterworth",
                "filter_order": filter_order,
                "number_of_passes": number_of_passes,
                "corner_frequency": freq,
            },
        )
    except BaseException as e:
        tr.fail(f"Lowpass filter failed with excpetion: {e}")
    return tr
