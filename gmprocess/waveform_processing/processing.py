#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Processing methods.
"""

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
from gmprocess.waveform_processing.processing_step import collect_processing_steps

all_processing_steps = collect_processing_steps()

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
            if step_name not in all_processing_steps:
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
                stream = all_processing_steps[step_name](stream, config=config)
            else:
                stream = all_processing_steps[step_name](
                    stream, **step_args, config=config
                )

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


def _add_step_arg(step_args, key, val):
    if step_args is None:
        return {key: val}
    else:
        step_args[key] = val
        return step_args
