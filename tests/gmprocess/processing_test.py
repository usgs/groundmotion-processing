#!/usr/bin/env python

# stdlib imports
import os.path
import glob
import logging

# third party imports
from obspy.core.utcdatetime import UTCDateTime
import numpy as np

# local imports
from gmprocess.io.read import read_data
from gmprocess.processing import process_streams
from gmprocess.logging import setup_logger
from gmprocess.stream import group_channels

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

    data_files = glob.glob(os.path.join(datadir, 'kiknet', 'AICH04*'))
    streams = [read_data(f) for f in data_files]
    grouped_streams = group_channels(streams)
    test = process_streams(grouped_streams, origin)

    logging.info('Testing trace: %s' % test[0][1])

    assert len(test) == 1
    assert len(test[0]) == 3

    # Apparently the traces end up in a different order on the Travis linux
    # container than on my local mac. So testing individual traces need to
    # not care about trace order.

    trace_maxes = np.sort([np.max(t.data) for t in test[0]])

    np.testing.assert_allclose(
        trace_maxes,
        np.array([1.30994939,  3.36651873,  4.87532321])
    )


if __name__ == '__main__':
    test_process_streams()
