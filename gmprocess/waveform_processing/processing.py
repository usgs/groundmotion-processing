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
from gmprocess.waveform_processing import corner_frequencies
from gmprocess.waveform_processing.baseline_correction import correct_baseline

# -----------------------------------------------------------------------------
# Note: no QA on following imports because they need to be in namespace to be
# discovered. They are not called directly so linters will think this is a
# mistake.
from gmprocess.waveform_processing.pretesting import (  # noqa: F401
    check_max_amplitude,
    check_sta_lta,
    check_free_field,
)
from gmprocess.waveform_processing.filtering import (  # noqa: F401
    lowpass_filter,
    highpass_filter,
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

M_TO_CM = 100.0

# List of processing steps that require an origin
# besides the arguments in the conf file.
REQ_ORIGIN = [
    "fit_spectra",
    "trim_multiple_events",
    "check_clipping",
    "get_corner_frequencies",
]


ABBREV_UNITS = {"ACC": "cm/s^2", "VEL": "cm/s", "DISP": "cm"}


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


def remove_response(
    st,
    pre_filt=True,
    f1=0.001,
    f2=0.005,
    f3=None,
    f4=None,
    water_level=60,
    inv=None,
    config=None,
):
    """
    Performs instrument response correction. If the response information is
    not already attached to the stream, then an inventory object must be
    provided. If the instrument is a strong-motion accelerometer, then
    tr.remove_sensitivity() will be used. High-gain seismometers will use
    tr.remove_response() with the defined pre-filter and water level.

    If f3 is Null it will be set to 0.9*fn, if f4 is Null it will be set to fn.

    Args:
        st (StationStream):
            Stream of data.
        pre_filt (bool):
            Apply a bandpass filter in frequency domain to the data before
            deconvolution?
        f1 (float):
            Frequency 1 for pre-filter.
        f2 (float):
            Frequency 2 for pre-filter.
        f3 (float):
            Frequency 3 for pre-filter.
        f4 (float):
            Frequency 4 for pre-filter.
        water_level (float):
            Water level for deconvolution.
        inv (obspy.core.inventory.inventory):
            Obspy inventory object containing response information.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Instrument-response-corrected stream.
    """
    output = "ACC"

    if inv is None:
        inv = st.getInventory()

    # Check if the response information is already attached in the trace stats
    for tr in st:

        # Check if this trace has already been converted to physical units
        if "remove_response" in tr.getProvenanceKeys():
            logging.debug(
                "Trace has already had instrument response removed. "
                "Nothing to be done."
            )
            continue

        f_n = 0.5 / tr.stats.delta
        if f3 is None:
            f3 = 0.9 * f_n
        if f4 is None:
            f4 = f_n
        if pre_filt:
            pre_filt_selected = (f1, f2, f3, f4)
        else:
            pre_filt_selected = None
        try:
            resp = inv.get_response(tr.id, tr.stats.starttime)
            paz = resp.get_paz()
            # Check if we have an instrument measuring velocity or accleration
            if tr.stats.channel[1] == "H":
                # Attempting to remove instrument response can cause a variety
                # errors due to bad response metadata
                try:
                    # Note: rater than set output to 'ACC' we are are setting
                    # it to 'VEl" and then differentiating.
                    tr.remove_response(
                        inventory=inv,
                        output="VEL",
                        water_level=water_level,
                        pre_filt=pre_filt_selected,
                        zero_mean=True,
                        taper=False,
                    )
                    tr.setProvenance(
                        "remove_response",
                        {
                            "method": "remove_response",
                            "input_units": "counts",
                            "output_units": ABBREV_UNITS["VEL"],
                            "water_level": water_level,
                            "pre_filt_freqs": str(pre_filt_selected),
                        },
                    )
                    diff_conf = config["differentiation"]
                    tr.differentiate(frequency=diff_conf["frequency"])
                    tr.data *= M_TO_CM  # Convert from m to cm
                    tr.stats.standard.units = ABBREV_UNITS[output]
                    tr.stats.standard.units_type = output.lower()
                    tr.stats.standard.process_level = PROCESS_LEVELS["V1"]
                except BaseException as e:
                    reason = (
                        "Encountered an error when attempting to remove "
                        "instrument response: %s" % str(e)
                    )
                    tr.fail(reason)
                    continue

                # Response removal can also result in NaN values due to bad
                # metadata, so check that data contains no NaN or inf values
                if not np.isfinite(tr.data).all():
                    reason = (
                        "Non-finite values encountered after removing "
                        "instrument response."
                    )
                    tr.fail(reason)
                    continue

            elif tr.stats.channel[1] == "N":
                try:
                    # If no poles and zeros are present in the xml file,
                    # use the sensitivity method.
                    if len(paz.poles) == 0 and len(paz.zeros) == 0:
                        tr.remove_sensitivity(inventory=inv)
                        tr.data *= M_TO_CM  # Convert from m to cm
                        tr.setProvenance(
                            "remove_response",
                            {
                                "method": "remove_sensitivity",
                                "input_units": "counts",
                                "output_units": ABBREV_UNITS[output],
                            },
                        )
                        tr.stats.standard.units = ABBREV_UNITS[output]
                        tr.stats.standard.units_type = output.lower()
                        tr.stats.standard.process_level = PROCESS_LEVELS["V1"]
                    else:
                        tr.remove_response(
                            inventory=inv,
                            output=output,
                            water_level=water_level,
                            pre_filt=pre_filt_selected,
                            zero_mean=True,
                            taper=False,
                        )
                        tr.data *= M_TO_CM  # Convert from m to cm
                        tr.setProvenance(
                            "remove_response",
                            {
                                "method": "remove_response",
                                "input_units": "counts",
                                "output_units": ABBREV_UNITS[output],
                                "water_level": water_level,
                                "pre_filt_freqs": str(pre_filt_selected),
                            },
                        )
                        tr.stats.standard.units = ABBREV_UNITS[output]
                        tr.stats.standard.units_type = output.lower()
                        tr.stats.standard.process_level = PROCESS_LEVELS["V1"]
                except BaseException as e:
                    reason = (
                        "Encountered an error when attempting to remove "
                        "instrument sensitivity: %s" % str(e)
                    )
                    tr.fail(reason)
                    continue
            else:
                reason = (
                    "This instrument type is not supported. "
                    "The instrument code must be either H "
                    "(high gain seismometer) or N (accelerometer)."
                )
                tr.fail(reason)
        except BaseException as e:
            logging.info(
                "Encountered an error when obtaining the poles and "
                "zeros information: %s. Now using remove_sensitivity "
                "instead of remove_response." % str(e)
            )
            tr.remove_sensitivity(inventory=inv)
            tr.data *= M_TO_CM  # Convert from m to cm
            tr.setProvenance(
                "remove_response",
                {
                    "method": "remove_sensitivity",
                    "input_units": "counts",
                    "output_units": ABBREV_UNITS[output],
                },
            )
            tr.stats.standard.units = ABBREV_UNITS[output]
            tr.stats.standard.units_type = output.lower()
            tr.stats.standard.process_level = PROCESS_LEVELS["V1"]

    return st


def lowpass_max_frequency(st, fn_fac=0.75, config=None):
    """
    Cap lowpass corner as a fraction of the Nyquist.

    Args:
        st (StationStream):
            Stream of data.
        fn_fac (float):
            Factor to be multiplied by the Nyquist to cap the lowpass filter.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Resampled stream.
    """
    if not st.passed:
        return st

    for tr in st:
        if tr.hasParameter("review"):
            rdict = tr.getParameter("review")
            if "corner_frequencies" in rdict:
                rev_fc_dict = rdict["corner_frequencies"]
                if "lowpass" in rev_fc_dict:
                    logging.warning(
                        f"Not applying lowpass_max_frequency for {tr} because the "
                        "lowpass filter corner was set by manual review."
                    )
                    continue

        fn = 0.5 * tr.stats.sampling_rate
        max_flp = fn * fn_fac
        freq_dict = tr.getParameter("corner_frequencies")
        if freq_dict["lowpass"] > max_flp:
            freq_dict["lowpass"] = max_flp
            tr.setParameter("corner_frequencies", freq_dict)

    return st


def min_sample_rate(st, min_sps=20.0, config=None):
    """
    Discard records if the sample rate doers not exceed minimum.

    Args:
        st (StationStream):
            Stream of data.
        min_sps (float):
            Minimum samples per second.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream checked for sample rate criteria.
    """
    if not st.passed:
        return st

    for tr in st:
        actual_sps = tr.stats.sampling_rate
        if actual_sps < min_sps:
            tr.fail(f"Minimum sample rate of {min_sps} not exceeded.")

    return st


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


def get_corner_frequencies(
    st,
    origin,
    method="snr",
    constant={"highpass": 0.08, "lowpass": 20.0},
    snr={"same_horiz": True},
    magnitude={
        "minmag": [-999.0, 3.5, 5.5],
        "highpass": [0.5, 0.3, 0.1],
        "lowpass": [25.0, 35.0, 40.0],
    },
    config=None,
):
    """
    Select corner frequencies.

    Args:
        st (StationStream):
            Stream of data.
        origin (ScalarEvent):
            ScalarEvent object.
        method (str):
            Which method to use; currently allowed "snr" or "constant".
        constant(dict):
            Dictionary of `constant` method config options.
        snr (dict):
            Dictionary of `snr` method config options.
        magnitude (dict):
            Dictionary of `magnitude` method config options.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        strea: Stream with selected corner frequencies added.
    """

    logging.debug("Setting corner frequencies...")
    if method == "constant":
        st = corner_frequencies.from_constant(st, **constant)
    elif method == "magnitude":
        st = corner_frequencies.from_magnitude(st, origin, **magnitude)
    elif method == "snr":
        st = corner_frequencies.from_snr(st, **snr)
        if snr["same_horiz"] and st.passed and st.num_horizontal > 1:
            lps = [tr.getParameter("corner_frequencies")["lowpass"] for tr in st]
            hps = [tr.getParameter("corner_frequencies")["highpass"] for tr in st]
            chs = [tr.stats.channel for tr in st]
            hlps = []
            hhps = []
            for i in range(len(chs)):
                if "z" not in chs[i].lower():
                    hlps.append(lps[i])
                    hhps.append(hps[i])
            llp = np.min(hlps)
            hhp = np.max(hhps)
            for i in range(len(chs)):
                if "z" not in chs[i].lower():
                    cfdict = st[i].getParameter("corner_frequencies")
                    cfdict["lowpass"] = llp
                    cfdict["highpass"] = hhp
                    st[i].setParameter("corner_frequencies", cfdict)
    else:
        raise ValueError(
            "Corner frequency 'method' must be one of: 'constant', 'magnitude', or "
            "'snr'."
        )

    # Replace corners set in manual review
    for tr in st:
        if tr.hasParameter("review"):
            review_dict = tr.getParameter("review")
            if "corner_frequencies" in review_dict:
                rev_fc_dict = review_dict["corner_frequencies"]
                if tr.hasParameter("corner_frequencies"):
                    base_fc_dict = tr.getParameter("corner_frequencies")
                    base_fc_dict["type"] = "reviewed"
                else:
                    base_fc_dict = {"type": "reviewed"}
                if ("highpass" in rev_fc_dict) or ("lowpass" in rev_fc_dict):
                    if "highpass" in rev_fc_dict:
                        base_fc_dict["highpass"] = rev_fc_dict["highpass"]
                    if "lowpass" in rev_fc_dict:
                        base_fc_dict["lowpass"] = rev_fc_dict["lowpass"]
                    tr.setParameter("corner_frequencies", base_fc_dict)
    return st


def check_instrument(st, n_max=3, n_min=2, require_two_horiz=True, config=None):
    """
    Test the channels of the station.

    The purpose of the maximum limit is to skip over stations with muliple
    strong motion instruments, which can occur with downhole or structural
    arrays since our code currently is not able to reliably group by location
    within an array.

    The purpose of the minimum and require_two_horiz checks are to ensure the
    channels are required for subsequent intensity measures such as ROTD.

    Args:
        st (StationStream):
            Stream of data.
        n_max (int):
            Maximum allowed number of streams; default to 3.
        n_min (int):
            Minimum allowed number of streams; default to 1.
        require_two_horiz (bool):
            Require two horizontal components; default to `False`.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        Stream with adjusted failed fields.
    """
    if not st.passed:
        return st

    if config is None:
        config = get_config()

    logging.debug("Starting check_instrument")
    logging.debug(f"len(st) = {len(st)}")

    for failed_test, message in [
        (len(st) > n_max, f"More than {n_max} traces in stream."),
        (len(st) < n_min, f"Less than {n_min} traces in stream."),
        (
            require_two_horiz and (st.num_horizontal != 2),
            "Not two horizontal components",
        ),
    ]:
        if failed_test:
            for tr in st:
                tr.fail(message)
            # Stop at first failed test
            break

    return st


def max_traces(st, n_max=3, config=None):
    """
    Reject a stream if it has more than n_max traces.

    The purpose of this is to skip over stations with muliple strong motion
    instruments, which can occur with downhole or structural arrays since our
    code currently is not able to reliably group by location within an array.

    Args:
        st (StationStream):
            Stream of data.
        n_max (int):
            Maximum allowed number of streams; default to 3.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        Stream with adjusted failed fields.
    """
    logging.warning(
        "This function is deprecated. Please replace with "
        "check_instrument, which includes additional "
        "functionality."
    )
    if not st.passed:
        return st

    logging.debug("Starting max_traces")
    logging.debug(f"len(st) = {len(st)}")
    if len(st) > n_max:
        for tr in st:
            tr.fail(f"More than {n_max} traces in stream.")
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
