#!/usr/bin/env python

# stdlib imports
import os.path
import glob
import logging

# third party imports
from obspy.core.utcdatetime import UTCDateTime
import numpy as np

# local imports
from gmprocess.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.processing import process_streams
from gmprocess.logging import setup_logger
from gmprocess.io.test_utils import read_data_dir
from gmprocess.config import get_config

homedir = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(homedir, '..', 'data')

setup_logger()


def test_process_streams():
    # Loma Prieta test station (nc216859)
    origin = {
        'eventid': 'test',
        'time': UTCDateTime('2000-10-16T13:30:00'),
        'magnitude': 7.3,
        'lat': 35.278,
        'lon': 133.345
    }

    data_files = glob.glob(os.path.join(
        datadir, 'kiknet', 'usp000a1b0', 'AICH04*'))
    data_files, origin = read_data_dir('geonet', 'us1000778i', '*.V1A')
    data_files, origin = read_data_dir('kiknet', 'usp000a1b0', 'AICH04*')
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    sc.describe()

    test = process_streams(sc, origin)

    logging.info('Testing trace: %s' % test[0][1])

    assert len(test) == 1
    assert len(test[0]) == 3

    # Apparently the traces end up in a different order on the Travis linux
    # container than on my local mac. So testing individual traces need to
    # not care about trace order.

    trace_maxes = np.sort([np.max(t.data) for t in test[0]])

    np.testing.assert_allclose(
        trace_maxes,
        np.array([1.30994939, 3.36651873, 4.87532321]),
        rtol=1e-5
    )


def test_free_field():
    data_files, origin = read_data_dir('kiknet', 'usp000hzq8')

    config = get_config()

    raw_streams = []
    for dfile in data_files:
        raw_streams += read_data(dfile)

    sc = StreamCollection(raw_streams)

    processed_streams = process_streams(sc, origin)

    # all of these streams should have failed for different reasons
    cmp_reasons = ['Failed sta/lta check.',
                   'Failed sta/lta check.',
                   'Failed free field sensor check.',
                   'Failed free field sensor check.']
    stream1 = find_stream(processed_streams, 'NGNH35', True)
    stream2 = find_stream(processed_streams, 'NGNH31', True)
    stream3 = find_stream(processed_streams, 'NGNH31', False)
    stream4 = find_stream(processed_streams, 'NGNH35', False)
    reasons = []
    reasons.append(stream1[0].getParameter('failure')['reason'])
    reasons.append(stream2[2].getParameter('failure')['reason'])
    reasons.append(stream3[0].getParameter('failure')['reason'])
    reasons.append(stream4[0].getParameter('failure')['reason'])
    for cmpreason, reason in zip(cmp_reasons, reasons):
        assert cmpreason == reason


def find_stream(streams, station, is_free):
    for stream in streams:
        c1 = stream[0].stats.station == station
        c2 = stream[0].free_field == is_free
        if c1 and c2:
            return stream


if __name__ == '__main__':
    test_free_field()
    test_process_streams()
