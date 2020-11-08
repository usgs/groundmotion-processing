#!/usr/bin/env python

from gmprocess.io.obspy.fdsn_fetcher import FDSNFetcher
from datetime import datetime
import os.path

# We can't run this test for regular CI purposes because it is inredibly slow
# and might even not be reliable, but it is useful to run occasionally so we
# are leaving it hear but prepending with an underscore so it doesn't get run
# automatically.


def test_fetcher():
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
    test_fetcher()
