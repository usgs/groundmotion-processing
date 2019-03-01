#!/usr/bin/env python
"""
Methods for handling/picking corner frequencies.
"""
import logging
import numpy as np

from obspy.signal.util import next_pow_2

from gmprocess.config import get_config
from gmprocess.utils import _get_provenance, _update_provenance
from gmprocess.smoothing.konno_ohmachi import konno_ohmachi_smooth

CONFIG = get_config()
# Options for tapering noise/signal windows
TAPER_WIDTH = 0.05
TAPER_TYPE = 'hann'
TAPER_SIDE = 'both'


def constant(st):
    """Use constant corner frequencies across all records.

    Args:
        st (obspy.core.stream.Stream):
            Stream of data.

    Returns:
        stream: stream with selected corner frequencies appended to records.
    """
    cf_config = CONFIG['corner_frequencies']
    for tr in st:
        tr = _update_provenance(
            tr, 'corner_frequencies',
            {
                'type': 'constant',
                'highpass': cf_config['constant']['highpass'],
                'lowpass': cf_config['constant']['lowpass']
            }
        )
    return st


def snr(st, threshold=3.0, max_low_freq=0.1, min_high_freq=5.0,
        bandwidth=20.0, same_horiz=True):
    """Use constant corner frequencies across all records.

    Args:
        st (obspy.core.stream.Stream):
            Stream of data.
        threshold (float):
            Minimum required SNR threshold for usable frequency bandwidth.
        max_low_freq (float):
            Maximum low frequency for SNR to exceed threshold.
        min_high_freq (float):
            Minimum high frequency for SNR to exceed threshold.
        bandwidth (float):
            Konno-Omachi  bandwidth parameter "b".
        same_horiz (bool):
            If True, horizontal traces in the stream must have the same
            corner frequencies.

    Returns:
        stream: stream with selected corner frequencies appended to records.
    """

    for tr in st:

        # Split the noise and signal into two separate traces
        split_prov = _get_provenance(tr, 'signal_split')[0]
        split_time = split_prov['split_time']
        noise = tr.copy().trim(endtime=split_time)
        signal = tr.copy().trim(starttime=split_time)

        # Taper both windows
        noise.taper(max_percentage=TAPER_WIDTH,
                    type=TAPER_TYPE,
                    side=TAPER_SIDE)
        signal.taper(max_percentage=TAPER_WIDTH,
                     type=TAPER_TYPE,
                     side=TAPER_SIDE)

        # Find the number of points for the Fourier transform
        nfft = max(next_pow_2(signal.stats.npts), next_pow_2(noise.stats.npts))

        # Transform to frequency domain and smooth spectra using
        # konno-ohmachi smoothing
        sig_spec_smooth, freqs_signal = fft_smooth(signal, nfft)
        noise_spec_smooth, freqs_noise = fft_smooth(noise, nfft)

        # remove the noise level from the spectrum of the signal window
        sig_spec_smooth -= noise_spec_smooth

        # Loop through frequencies to find low corner and high corner
        lows = []
        highs = []
        have_low = False
        for idx, freq in enumerate(freqs_signal):
            if have_low is False:
                if ((sig_spec_smooth[idx] / noise_spec_smooth[idx]) >=
                        threshold):
                    lows.append(freq)
                    have_low = True
                else:
                    continue
            else:
                if (sig_spec_smooth[idx] / noise_spec_smooth[idx]) < threshold:
                    highs.append(freq)
                    have_low = False
                else:
                    continue

        # Swap the highs and lows if our SNR at the first frequency was
        # above the threshold
        if sig_spec_smooth[0] / noise_spec_smooth[0] >= threshold:
            lows, highs = highs, lows

        # If we didn't find any corners
        if not lows:
            logging.info('Removing trace: %s (failed SNR check)' % tr)
            st.remove(tr)
            continue

        # If we find an extra low, add another high for the maximum frequency
        if len(lows) > len(highs):
            highs.append(max(freqs_signal))

        # Check if any of the low/high pairs are valid
        found_valid = False
        for idx, val in enumerate(lows):
            if (val <= max_low_freq and highs[idx] > min_high_freq):
                low_corner = val
                high_corner = highs[idx]
                found_valid = True

        if found_valid:
            tr = _update_provenance(
                tr, 'corner_frequencies',
                {
                    'type': 'snr',
                    'highpass': low_corner,
                    'lowpass': high_corner
                }
            )
        else:
            logging.info('Removing trace: %s (failed SNR check)' % tr)
            st.remove(tr)

    if same_horiz:

        st_horiz = st.select(channel='??[12EN]')
        # Make sure that horiztontal traces in the stream have the same corner
        # frequencies, if desired.
        corner_prov = _get_provenance(tr, 'corner_frequencies')[0]
        highpass_freqs = [corner_prov['highpass'] for tr in st_horiz]
        lowpass_freqs = [corner_prov['lowpass'] for tr in st_horiz]

        # For all traces in the stream, set highpass corner to highest high
        # and set the lowpass corner to the lowest low
        for tr in st_horiz:
            _update_provenance(
                tr, 'corner_frequencies',
                {
                    'type': 'snr',
                    'highpass': min(highpass_freqs),
                    'lowpass': max(lowpass_freqs)
                }
            )

    return st


def fft_smooth(trace, nfft):
    """
    Pads a trace to the nearest upper power of 2, takes the FFT, and
    smooths the amplitude spectra following the algorithm of
    Konno and Ohmachi.

    Args:
        trace (obspy.core.trace.Trace): Trace of strong motion data.
        nfft (int): Number of data points for the fourier transform.

    Returns:
        numpy.ndarray: Smoothed amplitude data and frequencies.
    """

    # Compute the FFT, normalizing by the number of data points
    spec = abs(np.fft.rfft(trace.data, n=nfft)) / nfft

    # Get the frequencies associated with the FFT
    freqs = np.fft.rfftfreq(nfft, 1 / trace.stats.sampling_rate)
    # Do a maximum of 301 K-O frequencies in the range of the fft freqs
    nkofreqs = min(nfft, 302) - 1
    ko_freqs = np.logspace(np.log10(freqs[1]), np.log10(freqs[-1]), nkofreqs)
    # An array to hold the output
    spec_smooth = np.empty_like(ko_freqs)

    # Konno Omachi Smoothing using 20 for bandwidth parameter
    konno_ohmachi_smooth(spec.astype(np.double), freqs, ko_freqs, spec_smooth,
                         20.0)
    return spec_smooth, ko_freqs
