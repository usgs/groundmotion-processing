#!/usr/bin/env python

import os.path
from gmprocess.io.obspy.core import read_obspy
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.processing import process_streams
import numpy as np
from numpy.testing import assert_almost_equal


def test_sac_csn():
    # This reads in example SAC data that does not have a separate metadata
    # file to meet the needs of the Community Seismic Network:
    # http://csn.caltech.edu/
    datafiles, origin = read_data_dir("csn", "ci38457511", "*.sac")
    datafiles.sort()
    traces = []
    for d in datafiles:
        traces.append(read_obspy(d)[0][0])

    tr_amax = np.zeros(len(traces))
    for i, tr in enumerate(traces):
        tr_amax[i] = np.max(np.abs(tr.data))

    target_amax = np.array([4.3384003e-09, 3.42233e-09, 1.0121747e-07])
    np.testing.assert_allclose(target_amax, tr_amax)


def test_channel_exclusion():
    exclude_patterns = ["*.*.??.???"]
    datafiles, origin = read_data_dir("fdsn", "se60247871", "US.LRAL*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 0

    exclude_patterns = ["*.*.??.LN?"]
    datafiles, origin = read_data_dir("fdsn", "se60247871", "US.LRAL*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 0

    exclude_patterns = ["*.*.??.LN?"]
    datafiles, origin = read_data_dir("fdsn", "nc72282711", "BK.CMB*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 3

    exclude_patterns = ["*.*.??.[BH]NZ"]
    datafiles, origin = read_data_dir("fdsn", "ci38445975", "CI.MIKB*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 4

    exclude_patterns = ["US.*.??.???"]
    datafiles, origin = read_data_dir("fdsn", "se60247871", "US.LRAL*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 0

    exclude_patterns = ["*.LRAL.??.???"]
    datafiles, origin = read_data_dir("fdsn", "se60247871", "US.LRAL*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 0

    exclude_patterns = ["*.*.40.???"]
    datafiles, origin = read_data_dir("fdsn", "nc73300395", "BK.VALB*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 0

    exclude_patterns = ["US.LRAL.20.LNZ"]
    datafiles, origin = read_data_dir("fdsn", "se60247871", "US.LRAL*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 2

    exclude_patterns = ["*.*.??.BN?", "*.*.??.HN?"]
    datafiles, origin = read_data_dir("fdsn", "ci38445975", "CI.MIKB*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 0


def test_weird_sensitivity():
    datafiles, origin = read_data_dir("fdsn", "us70008dx7", "SL.KOGS*.mseed")
    streams = []
    for datafile in datafiles:
        streams += read_obspy(datafile)
    sc = StreamCollection(streams)
    psc = process_streams(sc, origin)
    channel = psc[0].select(component="E")[0]
    assert_almost_equal(channel.data.max(), 62900.197618074293)


def test():
    datafiles, origin = read_data_dir("fdsn", "nc72282711", "BK.CMB*.mseed")
    streams = []
    for datafile in datafiles:
        streams += read_obspy(datafile)

    assert streams[0].get_id() == "BK.CMB.HN"

    datafiles, origin = read_data_dir("fdsn", "nc72282711", "TA.M04C*.mseed")
    streams = []
    for datafile in datafiles:
        streams += read_obspy(datafile)

    assert streams[0].get_id() == "TA.M04C.HN"

    # test assignment of Z channel
    datafiles, origin = read_data_dir("fdsn", "nc73300395", "BK.VALB*.mseed")
    streams = []
    for datafile in datafiles:
        streams += read_obspy(datafile)

    # get all channel names
    channels = sorted([st[0].stats.channel for st in streams])
    assert channels == ["HN2", "HN3", "HNZ"]

    # DEBUGGING
    # sc = StreamCollection(streams)
    # process_streams(sc, origin)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_sac_csn()
    test_channel_exclusion()
    test_weird_sensitivity()
    test()
