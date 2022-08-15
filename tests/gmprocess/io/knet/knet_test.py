#!/usr/bin/env python

import os.path
import numpy as np
from gmprocess.io.knet.core import is_knet, read_knet
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.constants import DATA_DIR


def test():
    datadir = DATA_DIR / "testdata" / "knet" / "us2000cnnl"

    knet_file1 = os.path.join(datadir, "AOM0051801241951.EW")
    knet_file2 = os.path.join(datadir, "AOM0051801241951.NS")
    knet_file3 = os.path.join(datadir, "AOM0051801241951.UD")
    assert is_knet(knet_file1)
    assert is_knet(os.path.abspath(__file__)) is False

    # test a knet file with npoints % 10 == 0
    stream1 = read_knet(knet_file1)[0]
    stream2 = read_knet(knet_file2)[0]
    stream3 = read_knet(knet_file3)[0]
    np.testing.assert_almost_equal(stream1[0].max(), -37.149, decimal=2)
    np.testing.assert_almost_equal(stream2[0].max(), 32.859, decimal=2)
    np.testing.assert_almost_equal(stream3[0].max(), 49.000, decimal=2)

    # test a file that has a number of points divisible by 8
    knet_file4 = os.path.join(datadir, "AOM0011801241951.EW")
    knet_file5 = os.path.join(datadir, "AOM0011801241951.NS")
    knet_file6 = os.path.join(datadir, "AOM0011801241951.UD")
    stream4 = read_knet(knet_file4)[0]
    stream5 = read_knet(knet_file5)[0]
    stream6 = read_knet(knet_file6)[0]
    np.testing.assert_almost_equal(stream4[0].max(), -11.435, decimal=2)
    np.testing.assert_almost_equal(stream5[0].max(), 12.412, decimal=2)
    np.testing.assert_almost_equal(stream6[0].max(), -9.284, decimal=2)

    # test that a file that is not knet format raises an Exception
    try:
        knet_files, _ = read_data_dir(
            "geonet", "nz2018p115908", "20161113_110256_WTMC_20.V1A"
        )

        knet_file = knet_files[0]
        read_knet(knet_file)[0]
        success = True
    except Exception:
        success = False
    assert not success

    # test some kiknet files
    datadir = DATA_DIR / "testdata" / "kiknet" / "usp000a1b0"
    kiknet_file1 = os.path.join(datadir, "AICH040010061330.EW2")
    kiknet_file2 = os.path.join(datadir, "AICH040010061330.NS2")
    kiknet_file3 = os.path.join(datadir, "AICH040010061330.UD2")
    assert is_knet(knet_file1)
    stream1 = read_knet(kiknet_file1)[0]  # east-west
    stream2 = read_knet(kiknet_file2)[0]  # north-south
    stream3 = read_knet(kiknet_file3)[0]  # vertical
    assert stream1[0].stats["channel"] == "HN2"
    assert stream2[0].stats["channel"] == "HN1"
    assert stream3[0].stats["channel"] == "HNZ"
    ewmax = np.abs(stream1[0].data).max()
    nsmax = np.abs(stream2[0].data).max()
    udmax = np.abs(stream3[0].data).max()
    np.testing.assert_almost_equal(ewmax, 5.020, decimal=1)
    np.testing.assert_almost_equal(nsmax, 10.749, decimal=1)
    np.testing.assert_almost_equal(udmax, 9.111, decimal=1)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test()
