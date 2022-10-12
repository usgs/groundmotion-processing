#!/usr/bin/env python

import os.path
import numpy as np
from gmprocess.io.esm.core import is_esm, read_esm
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.constants import TEST_DATA_DIR


def test():
    datadir = str(TEST_DATA_DIR / "esm" / "us60004wsq")

    esm_file1 = os.path.join(datadir, "HI.ARS1..HNE.D.20190728.160908.C.ACC.ASC")
    esm_file2 = os.path.join(datadir, "HI.ARS1..HNN.D.20190728.160908.C.ACC.ASC")
    esm_file3 = os.path.join(datadir, "HI.ARS1..HNZ.D.20190728.160908.C.ACC.ASC")
    assert is_esm(esm_file1)
    try:
        assert is_esm(os.path.abspath(__file__))
    except AssertionError:
        pass

    # test a esm file with npoints % 10 == 0
    stream1 = read_esm(esm_file1)[0]
    stream2 = read_esm(esm_file2)[0]
    stream3 = read_esm(esm_file3)[0]
    np.testing.assert_almost_equal(stream1[0].max(), 0.300022, decimal=2)
    np.testing.assert_almost_equal(stream2[0].max(), 0.359017, decimal=2)
    np.testing.assert_almost_equal(stream3[0].max(), 0.202093, decimal=2)

    # test that a file that is not esm format raises an Exception
    try:
        esm_files, _ = read_data_dir(
            "geonet", "nz2018p115908", "20161113_110256_WTMC_20.V1A"
        )

        esm_file = esm_files[0]
        read_esm(esm_file)[0]
        success = True
    except Exception:
        success = False
    assert not success


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test()
