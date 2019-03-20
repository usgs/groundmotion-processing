#!/usr/bin/env python

import sys
from gmprocess.io.geonet.geonet_fetcher import GeoNetFetcher
from datetime import datetime, timedelta
import os.path

import numpy as np


def fetcher_test():
    rawdir = os.path.join(os.path.expanduser('~'), 'tmp', 'geonet')
    # test when there is only one matching event
    eqdict = {'id': 'usp000hk1b',
              'time': datetime(2010, 9, 1, 21, 24, 45),
              'lat': -40.019,
              'lon': 172.999,
              'depth': 52.8,
              'mag': 4.2}

    fetcher = GeoNetFetcher(eqdict['time'],
                            eqdict['lat'],
                            eqdict['lon'],
                            eqdict['depth'],
                            eqdict['mag'],
                            rawdir=rawdir)
    events = fetcher.getMatchingEvents(solve=False)
    assert len(events) == 1
    stream_collection = fetcher.retrieveData(events[0])
    assert len(stream_collection) == 4

    # test the solver - NZ has two events one second apart (we only have one)
    eqdict = {'id': 'us10007db8',
              'time': datetime(2016, 11, 13, 11, 19, 34),
              'lat': -42.213,
              'lon': 173.432,
              'depth': 10.0,
              'mag': 5.5}
    fetcher = GeoNetFetcher(eqdict['time'],
                            eqdict['lat'],
                            eqdict['lon'],
                            eqdict['depth'],
                            eqdict['mag'],
                            dt=60,
                            rawdir=rawdir)
    events = fetcher.getMatchingEvents(solve=False)
    assert len(events) == 3
    events = fetcher.getMatchingEvents(solve=True)
    assert len(events) == 1
    stream_collection = fetcher.retrieveData(events[0])
    assert len(stream_collection) == 15


if __name__ == '__main__':
    fetcher_test()
