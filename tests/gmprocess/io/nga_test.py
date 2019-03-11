#!/usr/bin/env python3
import os
import numpy as np
from gmprocess.io.read import read_data
from gmprocess.io.nga import get_nga_record_sequence_no


def test_get_nga_record_sequence_no():

    homedir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(
        homedir, '..', '..', 'data', 'usc', 'ci3144585', '017m30cc.y0a')
    st = read_data(datafile)[0]

    # Test when a single record is found
    assert get_nga_record_sequence_no(st, 'Northridge-01') == 960

    # Test when no records are found
    assert np.isnan(get_nga_record_sequence_no(st, 'Northridge-01', 1))

    # Test when multiple records are found
    assert np.isnan(get_nga_record_sequence_no(st, 'Northridge-01', 10000))


if __name__ == '__main__':
    test_get_nga_record_sequence_no()
