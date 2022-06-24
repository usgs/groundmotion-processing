#!/usr/bin/env python

import sys
from gmprocess.io.knet.knet_fetcher import KNETFetcher, JST_OFFSET
from datetime import datetime, timedelta
import os.path


def fetcher_test(user, passwd):
    # 2019 - 03 - 02 03: 22: 52
    utime = datetime(2019, 3, 2, 3, 22, 52)
    eqlat = 41.934
    eqlon = 146.948
    eqdepth = 10.0
    eqmag = 6.0
    rawdir = os.path.join(os.path.expanduser("~"), "tmp", "knet")
    fetcher = KNETFetcher(
        utime, eqlat, eqlon, eqdepth, eqmag, user=user, password=passwd, rawdir=rawdir
    )
    events = fetcher.getMatchingEvents(solve=False)
    assert len(events) == 1
    assert events[0]["mag"] == 6.2
    stream_collection = fetcher.retrieveData(events[0])
    assert len(stream_collection) == 43

    utime = datetime(2018, 3, 29, 7, 21, 0) - timedelta(seconds=JST_OFFSET)
    eqlat = 34.23
    eqlon = 135.17
    eqdepth = 5.0
    eqmag = 2.8
    rawdir = os.path.join(os.path.expanduser("~"), "tmp", "knet")
    fetcher = KNETFetcher(
        utime,
        eqlat,
        eqlon,
        eqdepth,
        eqmag,
        user=user,
        password=passwd,
        rawdir=rawdir,
        dt=125,
    )
    events = fetcher.getMatchingEvents(solve=True)
    stream_collection = fetcher.retrieveData(events[0])
    assert len(stream_collection) == 78


if __name__ == "__main__":
    username = sys.argv[1]
    passwd = sys.argv[2]
    fetcher_test(username, passwd)
