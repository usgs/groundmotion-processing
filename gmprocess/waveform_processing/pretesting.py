#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pretesting methods.
"""

from obspy.signal.trigger import classic_sta_lta


def check_free_field(st, reject_non_free_field=False):
    """
    Checks free field status of stream.

    Args:
        st (obspy.core.stream.Stream):
            Stream of data.
        reject_non_free_field (bool):
            Should non free-field stations be failed?

    Returns:
        Stream that has been checked for free field status.
    """
    if not st.passed:
        return st

    for trace in st:
        if not trace.free_field and reject_non_free_field:
            trace.fail('Failed free field sensor check.')

    return st


def check_sta_lta(st, sta_length=1.0, lta_length=20.0, threshold=5.0):
    '''
    Checks that the maximum STA/LTA ratio for AT LEAST ONE of the stream's
    traces is above a certain threshold.

    Args:
        st (obspy.core.stream.Stream):
            Stream of data.
        sta_length (float):
            Length of time window for STA (seconds).
        lta_length (float):
            Length of time window for LTA (seconds).
        threshold (float):
            Required maximum STA/LTA ratio to pass the test.

    Returns:
        Stream that has been checked for sta/lta requirements.
    '''
    if not st.passed:
        return st

    for tr in st:
        sr = tr.stats.sampling_rate
        nlta = lta_length * sr + 1
        if len(tr) >= nlta:
            sta_lta = classic_sta_lta(tr.data, sta_length * sr + 1, nlta)
            if sta_lta.max() < threshold:
                tr.fail('Failed sta/lta check because threshold sta/lta '
                        'is not exceeded.')
        else:
            tr.fail('Failed sta/lta check because record length is shorter '
                    'than lta length.')

    return st


def check_max_amplitude(st, min=5, max=2e6):
    """
    Checks that the maximum amplitude of the traces in the stream are ALL
    within a defined range. Only applied to counts/raw data.

    Args:
        st (obspy.core.stream.Stream):
            Stream of data.
        min (float):
            Minimum amplitude for the acceptable range. Default is 5.
        max (float):
            Maximum amplitude for the acceptable range. Default is 2e6.

    Returns:
        Stream that has been checked for maximum amplitude criteria.
    """
    if not st.passed:
        return st

    for tr in st:
        # Only perform amplitude/clipping check if data has not been converted
        # to physical units
        if 'remove_response' not in tr.getProvenanceKeys():
            if (abs(tr.max()) < float(min) or
                    abs(tr.max()) > float(max)):
                tr.fail('Failed max amplitude check.')

    return st
