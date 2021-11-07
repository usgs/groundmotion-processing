#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np

from gmprocess.utils.test_utils import read_data_dir
from gmprocess.io.read import read_data


def test_uneven_samples():
    file1, _ = read_data_dir(
        'dmg', 'ci3031425',
        files=['NEWPORT.RAW'])
    test1 = read_data(file1[0])
    prov_resample = test1[0][0].getProvenance('resample')
    np.testing.assert_allclose(
        prov_resample[0]['nominal_sps'],
        201.32337744591487
    )


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_uneven_samples()
