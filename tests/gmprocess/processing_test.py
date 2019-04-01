#!/usr/bin/env python

# stdlib imports
import os
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

    data_files, origin = read_data_dir('geonet', 'us1000778i', '*.V1A')
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    sc.describe()

    test = process_streams(sc, origin)

    logging.info('Testing trace: %s' % test[0][1])

    assert len(test) == 3
    assert len(test[0]) == 3
    assert len(test[1]) == 3
    assert len(test[2]) == 3

    # Apparently the traces end up in a different order on the Travis linux
    # container than on my local mac. So testing individual traces need to
    # not care about trace order.

    trace_maxes = np.sort([np.max(np.abs(t.data)) for t in test[0]])

    np.testing.assert_allclose(
        trace_maxes,
        np.array([157.82909426, 240.36582093, 263.7063879]),
        rtol=1e-5
    )


def test_free_field():
    data_files, origin = read_data_dir('kiknet', 'usp000hzq8')

    raw_streams = []
    for dfile in data_files:
        raw_streams += read_data(dfile)

    sc = StreamCollection(raw_streams)

    processed_streams = process_streams(sc, origin)

    # all of these streams should have failed for different reasons
    npassed = np.sum([pstream.passed for pstream in processed_streams])
    assert npassed == 0
    for pstream in processed_streams:
        is_free = pstream[0].free_field
        reason = ''
        for trace in pstream:
            if trace.hasParameter('failure'):
                reason = trace.getParameter('failure')['reason']
                break
        if is_free:
            assert reason.startswith('Failed sta/lta check')
        else:
            assert reason == 'Failed free field sensor check.'


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_process_streams()
    test_free_field()
