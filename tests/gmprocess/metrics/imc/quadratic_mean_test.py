#!/usr/bin/env python

# third party imports
import numpy as np

# local imports
from gmprocess.metrics.combination.quadratic_mean import Quadratic_Mean


def test_quadratic_mean():
    trace1 = [1, 2, 3]
    trace2 = [4, 5, 6]


    # Test valid
    target = [np.sqrt(0.5*(1**2+4**2)), np.sqrt(0.5*(2**2+5**2)),
            np.sqrt(0.5*(3**2+6**2))]
    gm_data = Quadratic_Mean([[], trace1, trace2]).result[1]
    np.testing.assert_array_equal(gm_data, target)

    # Test invalid\
    failed = False
    try:
        gm_data = Quadratic_Mean({'HN1': 1, 'HNZ': 2})
    except:
        failed = True
    assert(failed == True)

    # Test invalid\
    failed = False
    try:
        gm_data = Quadratic_Mean({'HN1': 1, 'HNZ': 2, 'HN2': 3, 'HN3': 4})
    except:
        failed = True
    assert(failed == True)


if __name__ == '__main__':
    test_quadratic_mean()
