#!/usr/bin/env python

from gmprocess.io.fdsn.fdsn_fetcher import FDSNFetcher
from datetime import datetime
import os.path


def fetcher_test():
    # 2014-08-24 10:20:44
    eid = 'nc72282711'
    utime = datetime(2014, 8, 24, 10, 20, 44)
    eqlat = 38.215
    eqlon = -122.312
    eqdepth = 11.1
    eqmag = 6.0
    rawdir = os.path.join(os.path.expanduser('~'), 'tmp', eid, 'raw')
    fetcher = FDSNFetcher(utime, eqlat, eqlon, eqdepth, eqmag,
                          rawdir=rawdir)
    stream_collection = fetcher.retrieveData()
    assert len(stream_collection) == 15


if __name__ == '__main__':
    fetcher_test()
