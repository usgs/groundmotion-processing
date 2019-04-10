#!/usr/bin/env python

# stdlib imports
import os
from collections import OrderedDict

# third party imports
import numpy as np
import pkg_resources

from gmprocess.io.smc.core import is_smc, read_smc
from gmprocess.streamcollection import StreamCollection


def test_smc():
    dpath = os.path.join('data', 'testdata', 'smc', 'nc216859')
    datadir = pkg_resources.resource_filename('gmprocess', dpath)

    files = OrderedDict([('0111a.smc', (1.5057E+0, -2.8745E-1)),
                         ('0111b.smc', (-1.2518E+1, -1.6806E+0)),
                         ('0111c.smc', (-5.8486E+0, -1.1594E+0))])

    streams = []
    for tfilename, accvals in files.items():
        filename = os.path.join(datadir, tfilename)
        assert is_smc(filename)

        # test acceleration from the file
        stream = read_smc(filename)[0]

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

    # test location override
    stream = read_smc(filename, location='test')[0]
    for trace in stream:
        assert trace.stats.location == 'test'

    newstreams = StreamCollection(streams)
    assert len(newstreams) == 1

    filename = os.path.join(datadir, '891018_1.sma-1.0444a.smc')
    try:
        stream = read_smc(filename)[0]
        success = True
    except Exception:
        success = False
    assert success == False


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_smc()
