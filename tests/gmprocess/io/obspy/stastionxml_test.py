#!/usr/bin/env python

import os.path
import numpy as np
from numpy.testing import assert_allclose

from gmprocess.waveform_processing.processing import process_streams
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.test_utils import read_data_dir


def test():
    # Read in data with only one stationxml entry
    data_files, origin = read_data_dir("station_xml_epochs", "nc73631381", "*.mseed")
    test_root = os.path.normpath(os.path.join(data_files[0], os.pardir))
    sc = StreamCollection.from_directory(test_root)
    psc = process_streams(sc, origin)

    # Read in data with all dates in stationxml
    data_files, origin = read_data_dir("station_xml_epochs", "nc73631381_ad", "*.mseed")
    test_root = os.path.normpath(os.path.join(data_files[0], os.pardir))
    sc_ad = StreamCollection.from_directory(test_root)
    psc_ad = process_streams(sc_ad, origin)

    single_maxes = np.sort([np.max(tr.data) for tr in psc[0]])
    alldates_maxes = np.sort([np.max(tr.data) for tr in psc_ad[0]])
    assert_allclose(single_maxes, alldates_maxes)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test()
