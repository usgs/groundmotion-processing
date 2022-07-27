#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Methods for handling/picking corner frequencies.
"""

import logging
import numpy as np

from gmprocess.waveform_processing.processing_step import ProcessingStep
from gmprocess.waveform_processing.snr import compute_snr_trace

# Options for tapering noise/signal windows
TAPER_WIDTH = 0.05
TAPER_TYPE = "hann"
TAPER_SIDE = "both"


@ProcessingStep
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
        st = from_constant(st, **constant)
    elif method == "magnitude":
        st = from_magnitude(st, origin, **magnitude)
    elif method == "snr":
        st = from_snr(st, **snr)
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


@ProcessingStep
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


def from_constant(st, highpass=0.08, lowpass=20.0):
    """Use constant corner frequencies across all records.

    Args:
        st (StationStream):
            Stream of data.
        highpass (float):
            Highpass corner frequency (Hz).
        lowpass (float):
            Lowpass corner frequency (Hz).

    Returns:
        stream: stream with selected corner frequencies appended to records.
    """
    for tr in st:
        tr.setParameter(
            "corner_frequencies",
            {"type": "constant", "highpass": highpass, "lowpass": lowpass},
        )
    return st


def from_magnitude(
    st,
    origin,
    minmag=[-999.0, 3.5, 5.5],
    highpass=[0.5, 0.3, 0.1],
    lowpass=[25.0, 35.0, 40.0],
):
    """Use constant corner frequencies across all records.

    Args:
        st (StationStream):
            Stream of data.
        origin (ScalarEvent):
            ScalarEvent object.
        highpass (float):
            Highpass corner frequency (Hz).
        lowpass (float):
            Lowpass corner frequency (Hz).

    Returns:
        stream: stream with selected corner frequencies appended to records.
    """
    mag = origin.magnitude
    max_idx = np.max(np.where(mag > np.array(minmag))[0])
    hp_select = highpass[max_idx]
    lp_select = lowpass[max_idx]
    for tr in st:
        tr.setParameter(
            "corner_frequencies",
            {"type": "magnitude", "highpass": hp_select, "lowpass": lp_select},
        )
    return st


def from_snr(st, same_horiz=True, bandwidth=20):
    """Set corner frequencies from SNR.

    Args:
        st (StationStream):
            Stream of data.
        same_horiz (bool):
            If True, horizontal traces in the stream must have the same
            corner frequencies.
        bandwidth (float):
            Konno-Omachi smoothing bandwidth parameter.

    Returns:
        stream: stream with selected corner frequencies appended to records.
    """
    for tr in st:
        # Check for prior calculation of 'snr'
        if not tr.hasCached("snr"):
            tr = compute_snr_trace(tr, bandwidth)

        # If the SNR doesn't exist then it must have failed because it didn't
        # have nough points in the noise or signal windows
        if not tr.hasParameter("failure"):
            snr_conf = tr.getParameter("snr_conf")
            threshold = snr_conf["threshold"]
            min_freq = snr_conf["min_freq"]
            max_freq = snr_conf["max_freq"]

            if tr.hasCached("snr"):
                snr_dict = tr.getCached("snr")
            else:
                tr.fail(
                    "Cannot use SNR to pick corners because SNR could not "
                    "be calculated."
                )
                continue

            snr = snr_dict["snr"]
            freq = snr_dict["freq"]

            # Loop through frequencies to find low corner and high corner
            lows = []
            highs = []
            have_low = False
            for idx, f in enumerate(freq):
                if not have_low:
                    if snr[idx] >= threshold:
                        lows.append(f)
                        have_low = True
                    else:
                        continue
                else:
                    if snr[idx] < threshold:
                        highs.append(f)
                        have_low = False
                    else:
                        continue

            # If we didn't find any corners
            if not lows:
                tr.fail("SNR not greater than required threshold.")
                continue

            # If we find an extra low, add another high for the maximum
            # frequency
            if len(lows) > len(highs):
                highs.append(max(freq))

            # Check if any of the low/high pairs are valid
            found_valid = False
            for idx, val in enumerate(lows):
                if val <= min_freq and highs[idx] > max_freq:
                    low_corner = val
                    high_corner = highs[idx]
                    found_valid = True

            if found_valid:
                # Check to make sure that the highpass corner frequency is not
                # less than 1 / the duration of the waveform
                duration = (
                    tr.getParameter("signal_end")["end_time"] - tr.stats.starttime
                )
                low_corner = max(1 / duration, low_corner)

                # Make sure highpass is greater than min freq of noise spectrum
                n_noise = len(tr.getCached("noise_trace")["data"])
                min_freq_noise = 1.0 / n_noise / tr.stats.delta
                freq_hp = max(low_corner, min_freq_noise)

                tr.setParameter(
                    "corner_frequencies",
                    {"type": "snr", "highpass": freq_hp, "lowpass": high_corner},
                )
            else:
                tr.fail("SNR not met within the required bandwidth.")
    return st
