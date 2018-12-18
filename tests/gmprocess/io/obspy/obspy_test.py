#!/usr/bin/env python

# stdlib imports
import os.path
from collections import OrderedDict

# third party imports
import numpy as np

from gmprocess.io.obspy.core import is_obspy, read_obspy
from gmprocess.stream import group_channels


def test_obspy():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    datadir = os.path.join(homedir, '..', '..', '..', 'data', 'obspy')

    files = OrderedDict([('51PJW_H1.mseed', (3.112445E-002, -8.906940E-001)),
                         ('51PJW_H2.mseed', (-4.037475E-004, 2.463697E-001)),
                         ('51PJW_Z.mseed', (7.293111E-003, -5.053943E-002))])

    streams = []
    for tfilename, accvals in files.items():
        filename = os.path.join(datadir, tfilename)
        assert is_obspy(filename)

        # test acceleration from the file
        stream = read_obspy(filename)

        # test for one trace per file
        assert stream.count() == 1

        # test that the traces are acceleration
        for trace in stream:
            assert trace.stats.standard.units == 'acc'

        # compare the start/end points
        np.testing.assert_almost_equal(accvals[0], stream[0].data[0])
        np.testing.assert_almost_equal(accvals[1], stream[0].data[-1])

        # append to list of streams, so we can make sure these group together
        streams.append(stream)

    newstreams = group_channels(streams)
    assert len(newstreams) == 1


if __name__ == '__main__':
    test_obspy()
