#!/usr/bin/env python

from gmprocess.io.nsmn.turkey_fetcher import TurkeyFetcher
from datetime import datetime
import os.path
import logging


def fetcher_test():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # 2019-03-21 05:51:10
    utime = datetime(2019, 3, 21, 5, 51, 10)
    eqlat = 38.676
    eqlon = 38.042
    eqdepth = 10.0
    eqmag = 4.4
    rawdir = os.path.join(os.path.expanduser('~'), 'tmp', 'turkey')
    fetcher = TurkeyFetcher(utime, eqlat, eqlon, eqdepth, eqmag,
                            rawdir=rawdir)
    events = fetcher.getMatchingEvents(solve=False)
    assert len(events) == 1
    assert events[0]['mag'] == 4.1
    stream_collection = fetcher.retrieveData(events[0])
    assert len(stream_collection) == 27


if __name__ == '__main__':
    fetcher_test()
