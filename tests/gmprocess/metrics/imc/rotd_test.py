#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from gmprocess.io.geonet.core import read_geonet
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace
from gmprocess.utils.constants import DATA_DIR


def test_rotd():
    datadir = DATA_DIR / "testdata" / "process"
    # Create a stream and station summary, convert from m/s^2 to cm/s^2 (GAL)
    osc1_data = np.genfromtxt(datadir / "ALCTENE.UW..sac.acc.final.txt")
    osc2_data = np.genfromtxt(datadir / "ALCTENN.UW..sac.acc.final.txt")
    osc1_data = osc1_data.T[1] * 100
    osc2_data = osc2_data.T[1] * 100
    tr1 = StationTrace(
        data=osc1_data,
        header={
            "channel": "HN1",
            "delta": 0.01,
            "npts": 24001,
            "standard": {
                "corner_frequency": np.nan,
                "station_name": "",
                "source": "json",
                "instrument": "",
                "instrument_period": np.nan,
                "source_format": "json",
                "comments": "",
                "source_file": "",
                "structure_type": "",
                "horizontal_orientation": np.nan,
                "vertical_orientation": np.nan,
                "sensor_serial_number": "",
                "process_level": "corrected physical units",
                "process_time": "",
                "units": "cm/s/s",
                "units_type": "acc",
                "instrument_sensitivity": np.nan,
                "volts_to_counts": np.nan,
                "instrument_damping": np.nan,
            },
        },
    )
    tr2 = StationTrace(
        data=osc2_data,
        header={
            "channel": "HN2",
            "delta": 0.01,
            "npts": 24001,
            "standard": {
                "corner_frequency": np.nan,
                "station_name": "",
                "source": "json",
                "instrument": "",
                "instrument_period": np.nan,
                "source_format": "json",
                "comments": "",
                "structure_type": "",
                "source_file": "",
                "horizontal_orientation": np.nan,
                "vertical_orientation": np.nan,
                "sensor_serial_number": "",
                "process_level": "corrected physical units",
                "process_time": "",
                "units": "cm/s/s",
                "units_type": "acc",
                "instrument_sensitivity": np.nan,
                "volts_to_counts": np.nan,
                "instrument_damping": np.nan,
            },
        },
    )
    st = StationStream([tr1, tr2])

    for tr in st:
        response = {"input_units": "counts", "output_units": "cm/s^2"}
        tr.setProvenance("remove_response", response)

    target_pga50 = 4.1221200279448444
    target_sa1050 = 10.716249471749395
    target_pgv50 = 6.2243050413999645
    target_sa0350 = 10.091461811808575
    target_sa3050 = 1.1232860465386469
    station = StationSummary.from_stream(
        st, ["rotd50"], ["pga", "pgv", "sa0.3", "sa1.0", "sa3.0"]
    )

    pgms = station.pgms
    pga = pgms.loc["PGA", "ROTD(50.0)"].Result
    pgv = pgms.loc["PGV", "ROTD(50.0)"].Result
    SA10 = pgms.loc["SA(1.000)", "ROTD(50.0)"].Result
    SA03 = pgms.loc["SA(0.300)", "ROTD(50.0)"].Result
    SA30 = pgms.loc["SA(3.000)", "ROTD(50.0)"].Result
    np.testing.assert_allclose(pga, target_pga50)
    np.testing.assert_allclose(SA10, target_sa1050)
    np.testing.assert_allclose(pgv, target_pgv50)
    np.testing.assert_allclose(SA03, target_sa0350)
    np.testing.assert_allclose(SA30, target_sa3050)


def test_exceptions():
    datafiles, _ = read_data_dir("geonet", "us1000778i", "20161113_110259_WTMC_20.V2A")
    datafile_v2 = datafiles[0]
    stream_v2 = read_geonet(datafile_v2)[0]
    stream1 = stream_v2.select(channel="HN1")
    pgms = StationSummary.from_stream(stream1, ["rotd50"], ["pga"]).pgms
    assert np.isnan(pgms.loc["PGA", "ROTD(50.0)"].Result)


if __name__ == "__main__":
    test_rotd()
    test_exceptions()
