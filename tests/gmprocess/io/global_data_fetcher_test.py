#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gmprocess.io.global_fetcher import fetch_data
from datetime import datetime
import os


def geonet():
    # GeoNet
    # 2019-02-28 19:55:34 (UTC)37.512°S 179.185°E10.0 km depth
    utime = datetime(2019, 2, 28, 19, 55, 34)
    eqlat = -37.512
    eqlon = 179.185
    eqdepth = 10.0
    eqmag = 5.1
    rawdir = os.path.join(os.path.expanduser('~'), 'tmp', 'geonet')
    streams = fetch_data(utime, eqlat, eqlon, eqdepth, eqmag,
                         rawdir=rawdir)
    assert len(streams) == 6


def knet():
    # M 5.8 - 134km E of Iwaki, Japan
    # 2019-03-10 17:10:52 (UTC)36.852°N 142.368°E14.7 km depth
    utime = datetime(2019, 3, 10, 17, 10, 52)
    eqlat = 36.852
    eqlon = 142.368
    eqdepth = 14.7
    eqmag = 5.8
    rawdir = os.path.join(os.path.expanduser('~'), 'tmp', 'knet')
    streams = fetch_data(utime, eqlat, eqlon, eqdepth, eqmag,
                         rawdir=rawdir)
    assert len(streams) == 139


def turkey():
    # Turkey
    # 2019-03-21 05:51:10
    utime = datetime(2019, 3, 21, 5, 51, 10)
    eqlat = 38.676
    eqlon = 38.042
    eqdepth = 10.0
    eqmag = 4.4
    rawdir = os.path.join(os.path.expanduser('~'), 'tmp', 'turkey')
    streams = fetch_data(utime, eqlat, eqlon, eqdepth, eqmag,
                         rawdir=rawdir)
    assert len(streams) == 27


def fdsn():
    # 2014-08-24 10:20:44
    eid = 'nc72282711'
    utime = datetime(2014, 8, 24, 10, 20, 44)
    eqlat = 38.215
    eqlon = -122.312
    eqdepth = 11.1
    eqmag = 6.0
    rawdir = os.path.join(os.path.expanduser('~'), 'tmp', eid, 'raw')
    stream_collection = fetch_data(utime, eqlat, eqlon, eqdepth, eqmag,
                                   rawdir=rawdir)
    assert len(stream_collection) == 15


if __name__ == '__main__':
    # os.environ['CALLED_FROM_PYTEST'] = 'True'
    fdsn()
    knet()
    turkey()
    geonet()
