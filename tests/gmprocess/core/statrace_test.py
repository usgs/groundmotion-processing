#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from obspy.core.utcdatetime import UTCDateTime


from gmprocess.core.stationtrace import StationTrace

from invutils import get_inventory


def test_trace():
    data = np.random.rand(1000)
    header = {
        "sampling_rate": 1,
        "npts": len(data),
        "network": "US",
        "location": "11",
        "station": "ABCD",
        "channel": "HN1",
        "starttime": UTCDateTime(2010, 1, 1, 0, 0, 0),
    }
    inventory = get_inventory()
    invtrace = StationTrace(data=data, header=header, inventory=inventory)
    invtrace.setProvenance("detrend", {"detrending_method": "demean"})
    invtrace.setParameter("failed", True)
    invtrace.setParameter("corner_frequencies", [1, 2, 3])
    invtrace.setParameter("metadata", {"name": "Fred"})

    assert invtrace.getProvenance("detrend")[0] == {"detrending_method": "demean"}
    assert invtrace.getParameter("failed")
    assert invtrace.getParameter("corner_frequencies") == [1, 2, 3]
    assert invtrace.getParameter("metadata") == {"name": "Fred"}

    prov = invtrace.getProvSeries()
    assert prov[0] == "demean"


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_trace()
