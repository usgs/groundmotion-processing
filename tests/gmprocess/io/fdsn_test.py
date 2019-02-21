#!/usr/bin/env python

import os
import numpy as np
from gmprocess.io.fdsn import request_raw_waveforms
from gmprocess import process

homedir = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(homedir, '..', '..', 'data', 'process')


def _test_fetch():
    nisqually_st = request_raw_waveforms('IRIS', '2001-02-28T18:54:32',
                                         47.149, -122.7266667,
                                         dist_max=0.4, after_time=120)[0]

    # Set one of the waveforms to have a clipped value
    nisqually_st[0].data[0] = 2000000
    clips_length = len(nisqually_st)

    for tr in nisqually_st:
        tr.detrend('demean')
    nisqually_clip_rm, nisqually_clip = process.remove_clipped(nisqually_st)
    assert len(nisqually_clip) != 0
    nisqually_resp_rm = process.instrument_response(
        nisqually_clip_rm, f1=0.02, f2=0.05)

    # Test that this stream we requested gives us the same PGA as
    # calculated previously
    test_fdsn = nisqually_resp_rm[3]
    np.testing.assert_allclose(abs(test_fdsn.max()), 1.48, atol=0.01)

    # Test to make sure that the clipped waveform was removed from the stream
    no_clips_length = len(nisqually_resp_rm)
    assert no_clips_length < clips_length

    # Set one of the traces to have a bad instrument code
    nisqually_st = request_raw_waveforms('IRIS', '2001-02-28T18:54:32',
                                         47.149, -122.7266667, after_time=120,
                                         stations=['ALCT'])[0]
    nisqually_st[0].stats.channel = 'EAZ'
    try:
        nisqually_resp_rm = process.instrument_response(
            nisqually_st, f1=0.02, f2=0.05)
        success = True
    except ValueError:
        success = False
    assert success is False


if __name__ == '__main__':
    test_fetch()
