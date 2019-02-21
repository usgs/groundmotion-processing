#!/usr/bin/env python
"""
Pretesting methods.
"""
import logging

from obspy.signal.trigger import classic_sta_lta


def check_sta_lta(st, sta_length=1.0, lta_length=20.0, threshold=5.0):
    '''
    Checks that the maximum STA/LTA ratio of the trace is above a certain
    threshold.

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
        stream: Stream with traces that meet the STA/LTA ratio criteria.
    '''
    for tr in st:
        sr = tr.stats.sampling_rate
        sta_lta = classic_sta_lta(tr, sta_length * sr, lta_length * sr)
        if max(sta_lta) < threshold:
            logging.info('Removing trace: %s (failed STA/LTA check)' % tr)
            st.remove(tr)
    return st


def check_max_amplitude(st, min=5, max=2e6):
    """
    Checks that the maximum amplitude of the trace is within a defined
    range.

    Args:
        st (obspy.core.stream.Stream):
            Stream of data.
        min (float):
            Minimum amplitude for the acceptable range. Default is 10e-7.
        max (float):
            Maximum amplitude for the acceptable range. Default is 5e3.

    Returns:
        stream: Stream with traces that meet the amplitude criteria.
    """
    for tr in st:
        logging.debug('%s max: %s' % (tr, tr.max()))
        if (abs(tr.max()) < float(min) or
                abs(tr.max()) > float(max)):
            logging.info('Removing trace: %s (failed amplitude check)' % tr)
            st.remove(tr)
    return st
