#!/usr/bin/env python

import os.path
import numpy as np
from gmprocess.io.knet.core import is_knet, read_knet


def test():
    # where is this script?
    homedir = os.path.dirname(os.path.abspath(__file__))

    datadir = os.path.join(homedir, '..', '..', '..',
                           'data', 'knet', 'us2000cnnl')
    knet_file1 = os.path.join(datadir, 'AOM0051801241951.EW')
    knet_file2 = os.path.join(datadir, 'AOM0051801241951.NS')
    knet_file3 = os.path.join(datadir, 'AOM0051801241951.UD')
    assert is_knet(knet_file1)
    try:
        assert is_knet(os.path.abspath(__file__))
    except AssertionError:
        assert 1 == 1

    # test a knet file with npoints % 10 == 0
    stream1 = read_knet(knet_file1)[0]
    stream2 = read_knet(knet_file2)[0]
    stream3 = read_knet(knet_file3)[0]
    np.testing.assert_almost_equal(stream1[0].max(), 29.070, decimal=2)
    np.testing.assert_almost_equal(stream2[0].max(), 28.821, decimal=2)
    np.testing.assert_almost_equal(stream3[0].max(), 11.817, decimal=2)

    # test a file that has a number of points divisible by 8
    knet_file4 = os.path.join(datadir, 'AOM0011801241951.EW')
    knet_file5 = os.path.join(datadir, 'AOM0011801241951.NS')
    knet_file6 = os.path.join(datadir, 'AOM0011801241951.UD')
    stream4 = read_knet(knet_file4)[0]
    stream5 = read_knet(knet_file5)[0]
    stream6 = read_knet(knet_file6)[0]
    np.testing.assert_almost_equal(stream4[0].max(), 4.078, decimal=2)
    np.testing.assert_almost_equal(stream5[0].max(), -4.954, decimal=2)
    np.testing.assert_almost_equal(stream6[0].max(), -2.240, decimal=2)

    # test that a file that is not knet format raises an Exception
    try:
        datadir = os.path.join(homedir, '..', '..', '..',
                               'data', 'geonet', 'nz2018p115908')
        knet_file = os.path.join(datadir, '20161113_110256_WTMC_20.V1A')
        read_knet(knet_file)[0]
        success = True
    except Exception:
        success = False
    assert not success

    # test some kiknet files
    datadir = os.path.join(homedir, '..', '..', '..',
                           'data', 'kiknet', 'usp000a1b0')
    kiknet_file1 = os.path.join(datadir, 'AICH040010061330.EW2')
    kiknet_file2 = os.path.join(datadir, 'AICH040010061330.NS2')
    kiknet_file3 = os.path.join(datadir, 'AICH040010061330.UD2')
    assert is_knet(knet_file1)
    stream1 = read_knet(kiknet_file1)[0]  # east-west
    stream2 = read_knet(kiknet_file2)[0]  # north-south
    stream3 = read_knet(kiknet_file3)[0]  # vertical
    assert stream1[0].stats['channel'] == 'HN2'
    assert stream2[0].stats['channel'] == 'HN1'
    assert stream3[0].stats['channel'] == 'HNZ'
    ewmax = np.abs(stream1[0].data).max()
    nsmax = np.abs(stream2[0].data).max()
    udmax = np.abs(stream3[0].data).max()
    np.testing.assert_almost_equal(ewmax, 3.896, decimal=1)
    np.testing.assert_almost_equal(nsmax, 5.605, decimal=1)
    np.testing.assert_almost_equal(udmax, 1.488, decimal=1)


if __name__ == '__main__':
    test()
