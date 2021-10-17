#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Methods for handling/picking corner frequencies.
"""

from gmprocess.waveform_processing.snr import compute_snr_trace

# Options for tapering noise/signal windows
TAPER_WIDTH = 0.05
TAPER_TYPE = 'hann'
TAPER_SIDE = 'both'


def get_constant(st, highpass=0.08, lowpass=20.0):
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
            'corner_frequencies',
            {
                'type': 'constant',
                'highpass': highpass,
                'lowpass': lowpass
            }
        )
    return st


def get_snr(st, same_horiz=True, bandwidth=20):
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
        if not tr.hasCached('snr'):
            tr = compute_snr_trace(tr, bandwidth)

        # If the SNR doesn't exist then it must have failed because it didn't
        # have nough points in the noise or signal windows
        if not tr.hasParameter('failure'):
            snr_conf = tr.getParameter('snr_conf')
            threshold = snr_conf['threshold']
            min_freq = snr_conf['min_freq']
            max_freq = snr_conf['max_freq']

            if tr.hasCached('snr'):
                snr_dict = tr.getCached('snr')
            else:
                tr.fail('Cannot use SNR to pick corners because SNR could not '
                        'be calculated.')
                continue

            snr = snr_dict['snr']
            freq = snr_dict['freq']

            # Loop through frequencies to find low corner and high corner
            lows = []
            highs = []
            have_low = False
            for idx, f in enumerate(freq):
                if have_low is False:
                    if (snr[idx] >= threshold):
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
                tr.fail('SNR not greater than required threshold.')
                continue

            # If we find an extra low, add another high for the maximum
            # frequency
            if len(lows) > len(highs):
                highs.append(max(freq))

            # Check if any of the low/high pairs are valid
            found_valid = False
            for idx, val in enumerate(lows):
                if (val <= min_freq and highs[idx] > max_freq):
                    low_corner = val
                    high_corner = highs[idx]
                    found_valid = True

            if found_valid:
                # Check to make sure that the highpass corner frequency is not
                # less than 1 / the duration of the waveform
                duration = tr.getParameter('signal_end')[
                    'end_time'] - tr.stats.starttime
                low_corner = max(1 / duration, low_corner)

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
    return st
