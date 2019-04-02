#!/usr/bin/env python3
import os
import numpy as np
from gmprocess.io.read import read_data
from gmprocess.io.nga import get_nga_record_sequence_no
from gmprocess.io.test_utils import read_data_dir


def test_get_nga_record_sequence_no():
    datafiles, _ = read_data_dir('usc', 'ci3144585', '017m30cc.y0a')
    st = read_data(datafiles[0])[0]

    # Test when a single record is found
    assert get_nga_record_sequence_no(st, 'Northridge-01') == 960

    # Test when no records are found
    assert np.isnan(get_nga_record_sequence_no(st, 'Northridge-01', 1))

    # Test when multiple records are found
    assert np.isnan(get_nga_record_sequence_no(st, 'Northridge-01', 10000))


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_get_nga_record_sequence_no()
