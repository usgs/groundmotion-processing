#!/usr/bin/env python

# stdlib imports
import warnings

# third party imports
import numpy as np

# local imports
from gmprocess.metrics.gather import gather_pgms


def test_gather():
    target_imts = ['pga', 'pgv', 'sa', 'fas', 'arias']
    target_imcs = ['CHANNELS', 'GMROTD', 'ROTD', 'RADIAL_TRANSVERSE',
            'GREATER_OF_TWO_HORIZONTALS', 'ARITHMETIC_MEAN', 'GEOMETRIC_MEAN',
            'QUADRATIC_MEAN']
    target_imcs = ['channels', 'gmrotd', 'rotd', 'radial_transverse',
            'greater_of_two_horizontals', 'arithmetic_mean', 'geometric_mean',
            'quadratic_mean']
    imts, imcs = gather_pgms()
    assert len(imts) == len(target_imts)
    assert len(imcs) == len(target_imcs)
    np.testing.assert_array_equal(np.sort(imts), np.sort(target_imts))
    np.testing.assert_array_equal(np.sort(imcs), np.sort(target_imcs))


if __name__ == '__main__':
    test_gather()
