#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from obspy.signal.util import next_pow_2

from gmprocess.waveform_processing.smoothing.konno_ohmachi import konno_ohmachi_smooth


def compute_and_smooth_spectrum(tr, bandwidth, section, window=None, nfft=None):
    """
    Compute raw and smoothed signal spectrum for a given trace.

    Args:
        tr (StationTrace):
           Trace of data. This is the trace where the Cache values will be set.
        bandwidth (float):
           Konno-Omachi smoothing bandwidth parameter.
        section (str):
            Determines the name for the spectrum located in the Cache. This is
            usually either "signal" or "noise".
        window (StationTrace):
            Smaller window of the trace for computing the spectrum (usually
            either the signal or noise window). If not provided, then the
            entire trace will be used.
        nfft (int):
            Number of data points for the Fourier Transform. If not provided,
            then the next power of 2 from the number of points in the trace
            is used.

    Returns:
        StationTrace with signal spectrum dictionaries added as trace
        parameters.

    """
    if nfft is None:
        nfft = next_pow_2(tr.stats.npts)
    if window is None:
        window = tr

    spec_raw, freqs_raw = compute_fft(window, nfft)
    spec_smooth, freqs_smooth = smooth_spectrum(spec_raw, freqs_raw, nfft, bandwidth)

    raw_dict = {"spec": spec_raw, "freq": freqs_raw}
    smooth_dict = {"spec": spec_smooth, "freq": freqs_smooth}

    tr.setCached(f"{section}_spectrum", raw_dict)
    tr.setCached(f"smooth_{section}_spectrum", smooth_dict)

    return tr


def compute_fft(trace, nfft):
    """
    Computes the FFT of a trace, given the number of points for the FFT.
    This uses our convention where we multiply the spectra by the sampling
    interval.

    Args:
        trace (StationTrace):
            Trace of strong motion data.
        nfft (int):
            Number of data points for the Fourier Transform.

    Returns:
        numpy.ndarray: Amplitude data and frequencies.
    """
    dt = trace.stats.delta
    spec = abs(np.fft.rfft(trace.data, n=nfft)) * dt
    freqs = np.fft.rfftfreq(nfft, dt)
    return spec, freqs


def smooth_spectrum(spec, freqs, nfft, bandwidth=20):
    """
    Smooths the amplitude spectrum following the algorithm of
    Konno and Ohmachi.

    Args:
        spec (numpy.ndarray):
            Spectral amplitude data.
        freqs (numpy.ndarray):
            Frequencies.
        nfft (int):
            Number of data points for the fourier transform.
        bandwidth (float):
            Konno-Omachi smoothing bandwidth parameter.

    Returns:
        numpy.ndarray: Smoothed amplitude data and frequencies.
    """

    # Do a maximum of 301 K-O frequencies in the range of the fft freqs
    nkofreqs = min(nfft, 302) - 1
    ko_freqs = np.logspace(np.log10(freqs[1]), np.log10(freqs[-1]), nkofreqs)
    # An array to hold the output
    spec_smooth = np.empty_like(ko_freqs)

    # Konno Omachi Smoothing
    konno_ohmachi_smooth(
        spec.astype(np.double), freqs, ko_freqs, spec_smooth, bandwidth
    )
    return spec_smooth, ko_freqs
