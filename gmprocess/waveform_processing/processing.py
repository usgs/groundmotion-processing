#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Processing methods.
"""

import numpy as np
import logging

from obspy.taup import TauPyModel

from gmprocess.core.stationtrace import PROCESS_LEVELS
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.core.streamarray import StreamArray
from gmprocess.utils.config import get_config
from gmprocess.waveform_processing.windows import (
    signal_split,
    signal_end,
    window_checks,
)
from gmprocess.waveform_processing.phase import create_travel_time_dataframe
from gmprocess.waveform_processing.baseline_correction import correct_baseline

# -----------------------------------------------------------------------------
# Note: no QA on following imports because they need to be in namespace to be
# discovered. They are not called directly so linters will think this is a
# mistake.
from gmprocess.waveform_processing.pretesting import (  # noqa: F401
    check_max_amplitude,
    check_sta_lta,
    check_free_field,
    check_instrument,
    max_traces,
    min_sample_rate,
)
from gmprocess.waveform_processing.corner_frequencies import (  # noqa: F401
    lowpass_filter,
    highpass_filter,
)
from gmprocess.waveform_processing.filtering import (  # noqa: F401
    get_corner_frequencies,
    lowpass_max_frequency,
)
from gmprocess.waveform_processing.taper import taper  # noqa: F401
from gmprocess.waveform_processing.adjust_highpass import (  # noqa: F401
    adjust_highpass_corner,
)
from gmprocess.waveform_processing.adjust_highpass_ridder import (  # noqa: F401
    ridder_fchp,
)
from gmprocess.waveform_processing.zero_crossings import (  # noqa: F401
    check_zero_crossings,
)
from gmprocess.waveform_processing.instrument_response import (  # noqa: F401
    remove_response,
)
from gmprocess.waveform_processing.nn_quality_assurance import NNet_QA  # noqa: F401
from gmprocess.waveform_processing.snr import compute_snr, snr_check  # noqa: F401
from gmprocess.waveform_processing.spectrum import fit_spectra  # noqa: F401
from gmprocess.waveform_processing.windows import (  # noqa: F401
    cut,
    trim_multiple_events,
)
from gmprocess.waveform_processing.clipping.clipping_check import (  # noqa: F401
    check_clipping,
)
from gmprocess.waveform_processing.sanity_checks import check_tail  # noqa: F401

# -----------------------------------------------------------------------------

# List of processing steps that require an origin
# besides the arguments in the conf file.
REQ_ORIGIN = [
    "fit_spectra",
    "trim_multiple_events",
    "check_clipping",
    "get_corner_frequencies",
]


def process_streams(streams, origin, config=None, old_streams=None):
    """Run processing steps from the config file.

    This method looks in the 'processing' config section and loops over those
    steps and hands off the config options to the appropriate prcessing method.
    Streams that fail any of the tests are kepth in the StreamCollection but
    the parameter 'passed_checks' is set to False and subsequent processing
    steps are not applied once a check has failed.

    Args:
        streams (StreamCollection):
            A StreamCollection object of unprocessed streams.
        origin (ScalarEvent):
            ScalarEvent object.
        config (dict):
            Configuration dictionary (or None). See get_config().
        old_streams (StreamCollection):
            A StreamCollection object of previously processed streams that contain
            manually reviewed information. None if not reprocessing.

    Returns:
        A StreamCollection object.
    """

    if not isinstance(streams, (StreamCollection, StreamArray)):
        raise ValueError("streams must be a StreamCollection instance.")

    if config is None:
        config = get_config()

    event_time = origin.time
    event_lon = origin.longitude
    event_lat = origin.latitude

    # -------------------------------------------------------------------------
    # Compute a travel-time matrix for interpolation later in the
    # trim_multiple events step
    if any("trim_multiple_events" in dict for dict in config["processing"]):
        travel_time_df, catalog = create_travel_time_dataframe(
            streams, **config["travel_time"]
        )

    window_conf = config["windows"]
    model = TauPyModel(config["pickers"]["travel_time"]["model"])

    for st in streams:
        logging.debug(f"Checking stream {st.get_id()}...")
        # Estimate noise/signal split time
        st = signal_split(st, origin, model, config=config)

        # Estimate end of signal
        end_conf = window_conf["signal_end"]
        event_mag = origin.magnitude
        st = signal_end(
            st,
            event_time=event_time,
            event_lon=event_lon,
            event_lat=event_lat,
            event_mag=event_mag,
            **end_conf,
        )
        wcheck_conf = window_conf["window_checks"]
        if wcheck_conf["enabled"]:
            st = window_checks(
                st,
                min_noise_duration=wcheck_conf["min_noise_duration"],
                min_signal_duration=wcheck_conf["min_signal_duration"],
            )

    # -------------------------------------------------------------------------
    # Begin processing steps
    processing_steps = config["processing"]

    # Loop over streams
    for i, stream in enumerate(streams):
        logging.info(f"Stream: {stream.get_id()}")
        # Check if we are reprocessing (indicated by presence of old_streams)
        if old_streams is not None:
            old_stream = old_streams[i]
            for j in range(len(old_stream)):
                tr_old = old_stream[j]
                # Check if old_streams have review parameters because it is not
                # guaranteed
                if tr_old.hasParameter("review"):
                    review_dict = tr_old.getParameter("review")
                    # Transfer review parameter from old stream to new
                    stream[j].setParameter("review", review_dict)
                    # Was it failed via manual review?
                    if "accepted" in review_dict:
                        if not review_dict["accepted"]:
                            stream[j].fail("Manual review")

        for processing_step_dict in processing_steps:

            key_list = list(processing_step_dict.keys())
            if len(key_list) != 1:
                raise ValueError("Each processing step must contain exactly one key.")
            step_name = key_list[0]

            logging.debug(f"Processing step: {step_name}")
            step_args = processing_step_dict[step_name]
            # Using globals doesn't seem like a great solution here, but it
            # works.
            if step_name not in globals():
                raise ValueError(f"Processing step {step_name} is not valid.")

            # Origin is required by some steps and has to be handled specially.
            # There must be a better solution for this...
            if step_name in REQ_ORIGIN:
                step_args = _add_step_arg(step_args, "origin", origin)
            if step_name == "trim_multiple_events":
                step_args["catalog"] = catalog
                step_args["travel_time_df"] = travel_time_df
            if step_name == "snr_check":
                step_args = _add_step_arg(step_args, "mag", origin.magnitude)

            if step_args is None:
                stream = globals()[step_name](stream, config=config)
            else:
                stream = globals()[step_name](stream, **step_args, config=config)

    # -------------------------------------------------------------------------
    # Begin colocated instrument selection
    if config["colocated"]["enabled"]:
        colocated_conf = config["colocated"].copy()
        colocated_conf.pop("enabled")
        if isinstance(streams, StreamCollection):
            streams.select_colocated(**colocated_conf, origin=origin)

    for st in streams:
        for tr in st:
            tr.stats.standard.process_level = PROCESS_LEVELS["V2"]

    logging.info("Finished processing streams.")
    return streams


def detrend(st, detrending_method=None, config=None):
    """
    Detrend stream.

    Args:
        st (StationStream):
            Stream of data.
        method (str): Method to detrend; valid options include the 'type'
            options supported by obspy.core.trace.Trace.detrend as well as:
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


def resample(st, new_sampling_rate=None, method=None, a=None, config=None):
    """
    Resample stream.

    Args:
        st (StationStream):
            Stream of data.
        sampling_rate (float):
            New sampling rate, in Hz.
        method (str):
            Method for interpolation. Currently only supports 'lanczos'.
        a (int):
            Width of the Lanczos window, in number of samples.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Resampled stream.
    """
    if not st.passed:
        return st

    if method != "lanczos":
        raise ValueError("Only lanczos interpolation method is supported.")

    for tr in st:
        tr.interpolate(sampling_rate=new_sampling_rate, method=method, a=a)
        tr.setProvenance("resample", {"new_sampling_rate": new_sampling_rate})

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


def _add_step_arg(step_args, key, val):
    if step_args is None:
        return {key: val}
    else:
        step_args[key] = val
        return step_args
