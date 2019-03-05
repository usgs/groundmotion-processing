#!/usr/bin/env python

# stdlib imports
import os.path
import warnings

# third party imports
import numpy as np
from obspy.core.stream import Stream
from obspy.core.trace import Trace

# local imports
from gmprocess.metrics.imc.geometric_mean import calculate_geometric_mean


def test_geometric_mean():
    trace1 = Trace(data=np.asarray([1, 2, 3]), header={'channel': 'H1'})
    trace2 = Trace(data=np.asarray([4, 5, 6]), header={'channel': 'H2'})
    trace3 = Trace(data=np.asarray([4, 5]), header={'channel': 'H2'})
    trace4 = Trace(data=np.asarray([4, 5, 6]), header={'channel': 'z'})
    valid_stream = Stream(traces=[trace1, trace2])
    one_horizontal = Stream(traces=[trace1, trace4])
    too_many_horizontals = Stream(traces=[trace1, trace2, trace3])
    uneven = Stream(traces=[trace1, trace3])

    # Test valid
    target = [np.sqrt(0.5*(1**2+4**2)), np.sqrt(0.5*(2**2+5**2)),
            np.sqrt(0.5*(3**2+6**2))]
    gm_data = calculate_geometric_mean(valid_stream, return_combined=True)
    np.testing.assert_array_equal(gm_data, target)
    gm_val = calculate_geometric_mean(valid_stream)
    np.testing.assert_array_equal(gm_val, np.max(target))

    # Test invalid
    for invalid in [one_horizontal, too_many_horizontals, uneven]:
        failed = False
        try:
            gm_data = calculate_geometric_mean(invalid)
        except:
            failed = True
        assert(failed == True)


if __name__ == '__main__':
    test_geometric_mean()
