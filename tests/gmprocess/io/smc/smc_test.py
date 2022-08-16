#!/usr/bin/env python

# stdlib imports
import os
from collections import OrderedDict

# third party imports
import numpy as np

from gmprocess.io.smc.core import is_smc, read_smc
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.constants import TEST_DATA_DIR


def test_smc():
    datadir = TEST_DATA_DIR / "smc" / "nc216859"

    files = OrderedDict(
        [
            ("0111a.smc", (1.5057e0, -2.8745e-1)),
            ("0111b.smc", (-1.2518e1, -1.6806e0)),
            ("0111c.smc", (-5.8486e0, -1.1594e0)),
        ]
    )

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
            assert trace.stats.standard.units_type == "acc"

        # compare the start/end points
        np.testing.assert_almost_equal(accvals[0], stream[0].data[0])
        np.testing.assert_almost_equal(accvals[1], stream[0].data[-1])

        # append to list of streams, so we can make sure these group together
        streams.append(stream)

    # test location override
    stream = read_smc(filename, location="test")[0]
    for trace in stream:
        assert trace.stats.location == "test"

    newstreams = StreamCollection(streams)
    assert len(newstreams) == 1

    filename = os.path.join(datadir, "891018_1.sma-1.0444a.smc")
    try:
        stream = read_smc(filename)[0]
        success = True
    except Exception:
        success = False
    assert success is False


def test_bad():
    datadir = TEST_DATA_DIR / "duplicate" / "general"
    tfile = "np01002r_4225a_u.smc"
    dfile = datadir / tfile
    try:
        streams = read_smc(dfile)
    except Exception as e:
        msg = str(e)
        if "nonsensical" not in msg:
            fmt = 'SMC read errored out for unexpected reason "%s"'
            raise AssertionError(fmt % msg)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_bad()
    test_smc()
