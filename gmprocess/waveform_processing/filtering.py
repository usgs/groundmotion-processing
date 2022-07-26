#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gmprocess.waveform_processing.processing_step import ProcessingStep


@ProcessingStep
def highpass_filter(
    st, frequency_domain=True, filter_order=5, number_of_passes=1, config=None
):
    """
    Highpass filter.

    Args:
        st (StationStream):
            Stream of data.
        frequency_domain (bool):
            If true, use gmprocess frequency domain implementation; if false, use ObsPy
            filters.
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
        tr = highpass_filter_trace(
            tr, frequency_domain, filter_order, number_of_passes, config
        )

    return st


@ProcessingStep
def highpass_filter_trace(
    tr, frequency_domain=True, filter_order=5, number_of_passes=1, config=None
):
    """
    Highpass filter.

    Args:
        tr (StationTrace):
            Stream of data.
        frequency_domain (bool):
            If true, use gmprocess frequency domain implementation; if false, use ObsPy
            filters.
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
            freq=freq,
            corners=filter_order,
            zerophase=zerophase,
            config=config,
            frequency_domain=frequency_domain,
        )

    except BaseException as e:
        tr.fail(f"Highpass filter failed with excpetion: {e}")
    return tr


@ProcessingStep
def lowpass_filter(
    st, frequency_domain=True, filter_order=5, number_of_passes=1, config=None
):
    """
    Lowpass filter.

    Args:
        st (StationStream):
            Stream of data.
        frequency_domain (bool):
            If true, use gmprocess frequency domain implementation; if false, use ObsPy
            filters.
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
        tr = lowpass_filter_trace(
            tr, frequency_domain, filter_order, number_of_passes, config
        )

    return st


@ProcessingStep
def lowpass_filter_trace(
    tr, frequency_domain, filter_order=5, number_of_passes=1, config=None
):
    """
    Lowpass filter.

    Args:
        tr (StationTrace):
            Stream of data.
        frequency_domain (bool):
            If true, use gmprocess frequency domain implementation; if false, use ObsPy
            filters.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.
        config (dict):
            Configuration dictionary (or None). See get_config().

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
        tr.filter(
            type="lowpass",
            freq=freq,
            corners=filter_order,
            zerophase=zerophase,
            config=config,
            frequency_domain=frequency_domain,
        )

    except BaseException as e:
        tr.fail(f"Lowpass filter failed with excpetion: {e}")
    return tr
