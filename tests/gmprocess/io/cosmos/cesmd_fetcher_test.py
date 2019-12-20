#!/usr/bin/env python

import sys
from gmprocess.io.cosmos.cesmd_fetcher import CESMDFetcher
from datetime import datetime, timedelta
import os.path


def fetcher_test(email):
    # 2019 - 03 - 02 03: 22: 52
    # 2014 - 08 - 24 10: 20: 44
    # 2019-10-15 19:42:30
    utime = datetime(2019, 10, 15, 19, 42, 30)
    eqlat = 36.646
    eqlon = -121.274
    eqdepth = 10.1
    eqmag = 4.7
    rawdir = os.path.join(os.path.expanduser('~'), 'tmp', 'cesmd', 'testevent')
    fetcher = CESMDFetcher(utime, eqlat, eqlon, eqdepth, eqmag,
                           email=email, rawdir=rawdir)
    events = fetcher.getMatchingEvents(solve=False)
    assert len(events) == 1
    assert events[0]['mag'] == eqmag
    stream_collection = fetcher.retrieveData(events[0])
    assert len(stream_collection) == 28

    utime = datetime(2018, 3, 29, 7, 21, 0) - timedelta(seconds=JST_OFFSET)
    eqlat = 34.23
    eqlon = 135.17
    eqdepth = 5.0
    eqmag = 2.8
    rawdir = os.path.join(os.path.expanduser('~'), 'tmp', 'knet')
    fetcher = KNETFetcher(utime, eqlat, eqlon, eqdepth, eqmag,
                          user=user, password=passwd, rawdir=rawdir, dt=125)
    events = fetcher.getMatchingEvents(solve=True)
    stream_collection = fetcher.retrieveData(events[0])
    assert len(stream_collection) == 78


if __name__ == '__main__':
    email = sys.argv[1]
    fetcher_test(email)
