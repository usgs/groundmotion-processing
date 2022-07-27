#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from obspy.signal.util import next_pow_2

from gmprocess.waveform_processing.fft import compute_and_smooth_spectrum
from gmprocess.waveform_processing.spectrum import brune_f0, moment_from_magnitude
from gmprocess.waveform_processing.processing_step import ProcessingStep


# Options for tapering noise/signal windows
TAPER_WIDTH = 0.05
TAPER_TYPE = "hann"
TAPER_SIDE = "both"
MIN_POINTS_IN_WINDOW = 10


@ProcessingStep
def compute_snr(st, bandwidth=20.0, config=None):
    """Compute SNR dictionaries for a stream, looping over all traces.

    Args:
        st (StationStream):
           Trace of data.
        bandwidth (float):
           Konno-Omachi smoothing bandwidth parameter.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream with SNR dictionaries added as trace parameters.
    """
    for tr in st:
        # Do we have estimates of the signal split time?
        compute_snr_trace(tr, bandwidth)
    return st


@ProcessingStep
def snr_check(
    st,
    mag,
    threshold=3.0,
    min_freq="f0",
    max_freq=5.0,
    f0_options={"stress_drop": 10, "shear_vel": 3.7, "ceiling": 2.0, "floor": 0.1},
    config=None,
):
    """Check signal-to-noise ratio.

    Requires noise/singal windowing to have succeeded.

    Args:
        st (StationStream):
           Trace of data.
        mag (float):
            Earthquake magnitude.
        threshold (float):
            Threshold SNR value.
        min_freq (float or str):
            Minimum frequency for threshold to be exeeded. If 'f0', then the
            Brune corner frequency will be used.
        max_freq (float):
            Maximum frequency for threshold to be exeeded.
        bandwidth (float):
            Konno-Omachi smoothing bandwidth parameter.
        f0_options (dict):
            Dictionary of f0 options (see config file).
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        trace: Trace with SNR check.
    """
    for tr in st:
        if tr.hasCached("snr"):
            snr_dict = tr.getCached("snr")
            snr = np.array(snr_dict["snr"])
            freq = np.array(snr_dict["freq"])

            # If min_freq is 'f0', then compute Brune corner frequency
            if min_freq == "f0":
                min_freq = brune_f0(
                    moment_from_magnitude(mag),
                    f0_options["stress_drop"],
                    f0_options["shear_vel"],
                )
                if min_freq < f0_options["floor"]:
                    min_freq = f0_options["floor"]
                if min_freq > f0_options["ceiling"]:
                    min_freq = f0_options["ceiling"]

            # Check if signal criteria is met
            mask = (freq >= min_freq) & (freq <= max_freq)
            if np.any(mask):
                min_snr = np.min(snr[mask])
            else:
                min_snr = 0

            if min_snr < threshold:
                tr.fail("Failed SNR check; SNR less than threshold.")
        snr_conf = {"threshold": threshold, "min_freq": min_freq, "max_freq": max_freq}
        tr.setParameter("snr_conf", snr_conf)
    return st


def compute_snr_trace(tr, bandwidth=20.0):
    """Compute SNR dictionaries for a trace.

    Args:
        bandwidth (float):
            Konno-Omachi smoothing bandwidth parameter.

    """
    if tr.hasParameter("signal_split"):
        # Split the noise and signal into two separate traces
        split_prov = tr.getParameter("signal_split")
        if isinstance(split_prov, list):
            split_prov = split_prov[0]
        split_time = split_prov["split_time"]
        noise = tr.copy().trim(endtime=split_time)
        signal = tr.copy().trim(starttime=split_time)

        tr.setCached("noise_trace", {"times": noise.times(), "data": noise.data})

        noise.detrend("demean")
        signal.detrend("demean")

        # Taper both windows
        noise.taper(max_percentage=TAPER_WIDTH, type=TAPER_TYPE, side=TAPER_SIDE)
        signal.taper(max_percentage=TAPER_WIDTH, type=TAPER_TYPE, side=TAPER_SIDE)

        # Check that there are a minimum number of points in the noise window
        if noise.stats.npts < MIN_POINTS_IN_WINDOW:
            # Fail the trace, but still compute the signal spectra
            # ** only fail here if it hasn't already failed; we do not yet
            # ** support tracking multiple fail reasons and I think it is
            # ** better to know the FIRST reason if I have to pick one.
            if not tr.hasParameter("failure"):
                tr.fail("Failed SNR check; Not enough points in noise window.")
            compute_and_smooth_spectrum(tr, bandwidth, "signal")
            return tr

        # Check that there are a minimum number of points in the noise window
        if signal.stats.npts < MIN_POINTS_IN_WINDOW:
            # Fail the trace, but still compute the signal spectra
            if not tr.hasParameter("failure"):
                tr.fail("Failed SNR check; Not enough points in signal window.")
            compute_and_smooth_spectrum(tr, bandwidth, "signal")
            return tr

        nfft = max(next_pow_2(signal.stats.npts), next_pow_2(noise.stats.npts))

        compute_and_smooth_spectrum(tr, bandwidth, "noise", noise, nfft)
        compute_and_smooth_spectrum(tr, bandwidth, "signal", signal, nfft)

        # For both the raw and smoothed spectra, subtract the noise spectrum
        # from the signal spectrum
        tr.setCached(
            "signal_spectrum",
            {
                "spec": (
                    tr.getCached("signal_spectrum")["spec"]
                    - tr.getCached("noise_spectrum")["spec"]
                ),
                "freq": tr.getCached("signal_spectrum")["freq"],
            },
        )
        tr.setCached(
            "smooth_signal_spectrum",
            {
                "spec": (
                    tr.getCached("smooth_signal_spectrum")["spec"]
                    - tr.getCached("smooth_noise_spectrum")["spec"]
                ),
                "freq": tr.getCached("smooth_signal_spectrum")["freq"],
            },
        )

        smooth_signal_spectrum = tr.getCached("smooth_signal_spectrum")["spec"]
        smooth_noise_spectrum = tr.getCached("smooth_noise_spectrum")["spec"]
        snr = smooth_signal_spectrum / smooth_noise_spectrum

        snr_dict = {"snr": snr, "freq": tr.getCached("smooth_signal_spectrum")["freq"]}
        tr.setCached("snr", snr_dict)

    else:
        # We do not have an estimate of the signal split time for this trace
        compute_and_smooth_spectrum(tr, bandwidth, "signal")

    return tr
