#!/usr/bin/env python
# -*- coding: utf-8 -*-

# third party imports
import numpy as np

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.metrics.station_summary import StationSummary


def test_gmrotd():
    datafiles, _ = read_data_dir("geonet", "us1000778i", "20161113_110259_WTMC_20.V2A")
    datafile_v2 = datafiles[0]

    stream_v2 = read_geonet(datafile_v2)[0]
    station_summary = StationSummary.from_stream(
        stream_v2, ["gmrotd0", "gmrotd50", "gmrotd100"], ["pga"]
    )
    pgms = station_summary.pgms
    assert "GMROTD(50.0)" in pgms.index.get_level_values(1)


def test_exceptions():
    datafiles, _ = read_data_dir("geonet", "us1000778i", "20161113_110259_WTMC_20.V2A")
    datafile_v2 = datafiles[0]
    stream_v2 = read_geonet(datafile_v2)[0]
    stream1 = stream_v2.select(channel="HN1")
    pgms = StationSummary.from_stream(stream1, ["gmrotd50"], ["pga"]).pgms
    assert np.isnan(pgms.Result.iloc[0])

    for trace in stream_v2:
        stream1.append(trace)
    pgms = StationSummary.from_stream(stream1, ["gmrotd50"], ["pga"]).pgms
    assert np.isnan(pgms.Result.iloc[0])


if __name__ == "__main__":
    test_gmrotd()
    test_exceptions()
