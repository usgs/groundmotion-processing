#!/usr/bin/env python
"""
Pretesting methods.
"""
import logging

from obspy.signal.trigger import classic_sta_lta


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
        bool: Did the stream pass the check?
    '''

    passed_checks = []
    for tr in st:
        sr = tr.stats.sampling_rate
        sta_lta = classic_sta_lta(tr, sta_length * sr + 1, lta_length * sr + 1)
        if max(sta_lta) >= threshold:
            passed = True
        else:
            passed = False
        passed_checks.append(passed)
        tr.setParameter('sta_lta_check_test', passed)

    all_passed = True
    if sum(passed_checks) < len(st):
        all_passed = False
        logging.info('Trace %s failed STA/LTA check.' % tr)
    for tr in st:
        tr.setParameter('passed_checks', all_passed)
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
        bool: Did the stream pass the check?
    """
    passed_checks = []
    for tr in st:
        if isinstance(tr.data[0], int):
            if (abs(tr.max()) < float(min) or
                    abs(tr.max()) > float(max)):
                logging.info(
                    'Removing trace: %s (failed amplitude check)' % tr)
                logging.debug('%s max: %s' % (tr, tr.max()))
                passed = False
            else:
                passed = True
            tr.setParameter('amp_check_test', passed)
        else:
            passed = True
        passed_checks.append(passed)

    all_passed = True
    if sum(passed_checks) < len(st):
        all_passed = False
        logging.info('Trace %s failed STA/LTA check.' % tr)
    for tr in st:
        tr.setParameter('passed_checks', all_passed)
    return st
