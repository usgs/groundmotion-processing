#!/usr/bin/env python

# stdlib imports
import os.path

# third party imports
import numpy as np
from obspy.core.stream import Stream
from obspy.core.trace import Trace

# local imports
from gmprocess.metrics.exception import PGMException
from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.station_summary import StationSummary


def test_gmrotd():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    datafile_v2 = os.path.join(homedir, '..', '..', 'data', 'geonet', 'us1000778i',
                               '20161113_110259_WTMC_20.V2A')
    stream_v2 = read_geonet(datafile_v2)[0]
    station_summary = StationSummary.from_stream(stream_v2,
                                                 ['gmrotd0', 'gmrotd50', 'gmrotd100'], ['pga'])


def test_exceptions():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    datafile_v2 = os.path.join(homedir, '..', '..', 'data', 'geonet', 'us1000778i',
                               '20161113_110259_WTMC_20.V2A')
    stream_v2 = read_geonet(datafile_v2)[0]
    stream1 = stream_v2.select(channel="HN1")
    try:
        StationSummary.from_stream(stream1, ['gmrotd50'], ['pga'])
        sucess = True
    except PGMException:
        sucess = False
    assert sucess == False

    for trace in stream_v2:
        stream1.append(trace)
    try:
        StationSummary.from_stream(stream1, ['gmrotd50'], ['pga'])
        sucess = True
    except PGMException:
        sucess = False
    assert sucess == False

    stream2 = Stream(
        [stream_v2.select(channel="HN1")[0],
            Trace(data=np.asarray([]), header={"channel": "HN2"})])
    try:
        StationSummary.from_stream(stream2, ['gmrotd50'], ['pga'])
        sucess = True
    except PGMException:
        sucess = False
    assert sucess == False


if __name__ == '__main__':
    test_gmrotd()
    test_exceptions()
