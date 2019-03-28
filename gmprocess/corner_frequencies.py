#!/usr/bin/env python
"""
Methods for handling/picking corner frequencies.
"""

from gmprocess.plot import summary_plot
from gmprocess.config import get_config
from gmprocess.snr import compute_snr

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
    config = get_config()
    cf_config = config['corner_frequencies']
    for tr in st:
        tr.setParameter(
            'corner_frequencies',
            {
                'type': 'constant',
                'highpass': cf_config['constant']['highpass'],
                'lowpass': cf_config['constant']['lowpass']
            }
        )
    return st


def snr(st, threshold=3.0, max_low_freq=0.1, min_high_freq=5.0,
        bandwidth=20.0, same_horiz=True, make_plots=False, plot_dir=None):
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
        make_plots (bool):
            If True, will save plots indicating signal and noise spectra, SNR,
            and the chosen corner frequencies. Saved to plot_dir.
        plot_dir (str):
            Directory for saving SNR plots.

    Returns:
        stream: stream with selected corner frequencies appended to records.
    """
    for tr in st:

        # Check for prior calculation of 'snr'
        if not tr.hasParameter('snr'):
            tr = compute_snr(tr)

        snr_dict = tr.getParameter('snr')
        snr = snr_dict['snr']
        freq = snr_dict['freq']

        # Loop through frequencies to find low corner and high corner
        lows = []
        highs = []
        have_low = False
        for idx, freq in enumerate(freq):
            if have_low is False:
                if ([idx] >= threshold):
                    lows.append(freq)
                    have_low = True
                else:
                    continue
            else:
                if snr[idx] < threshold:
                    highs.append(freq)
                    have_low = False
                else:
                    continue

        # If we didn't find any corners
        if not lows:
            tr.fail('SNR not greater than required threshold.')
#            summary_plot(tr, sig_spec, sig_spec_smooth, noise_spec,
#                         noise_spec_smooth, sig_spec_freqs, freqs_signal,
#                         threshold, plot_dir)
            continue

        # If we find an extra low, add another high for the maximum frequency
        if len(lows) > len(highs):
            highs.append(max(freq))

        # Check if any of the low/high pairs are valid
        found_valid = False
        for idx, val in enumerate(lows):
            if (val <= max_low_freq and highs[idx] > min_high_freq):
                low_corner = val
                high_corner = highs[idx]
                found_valid = True

        if found_valid:
            tr.setParameter(
                'corner_frequencies',
                {
                    'type': 'snr',
                    'highpass': low_corner,
                    'lowpass': high_corner
                }
            )
        else:
            tr.fail('SNR not met within the required bandwidth.')
