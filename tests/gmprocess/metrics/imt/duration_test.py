#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import numpy as np

from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace
from gmprocess.metrics.reduction.duration import Duration
from gmprocess.utils.constants import TEST_DATA_DIR


def test_duration():
    data_file = TEST_DATA_DIR / "duration_data.json"
    with open(str(data_file), "rt", encoding="utf-8") as f:
        jdict = json.load(f)

    time = np.array(jdict["time"])
    # input output is m/s/s
    acc = np.array(jdict["acc"]) / 100
    target_d595 = jdict["d595"]
    delta = time[2] - time[1]
    sr = 1 / delta
    header = {
        "delta": delta,
        "sampling_rate": sr,
        "npts": len(acc),
        "channel": "HN1",
        "standard": {
            "corner_frequency": np.nan,
            "station_name": "",
            "source": "json",
            "source_file": "",
            "instrument": "",
            "instrument_period": np.nan,
            "source_format": "json",
            "comments": "",
            "structure_type": "",
            "sensor_serial_number": "",
            "process_level": "raw counts",
            "process_time": "",
            "horizontal_orientation": np.nan,
            "vertical_orientation": np.nan,
            "units": "m/s/s",
            "units_type": "acc",
            "instrument_sensitivity": np.nan,
            "volts_to_counts": np.nan,
            "instrument_damping": np.nan,
        },
    }
    # input is cm/s/s output is m/s/s
    trace = StationTrace(data=acc * 100, header=header)
    trace2 = trace.copy()
    trace2.stats.channel = "HN2"
    stream = StationStream([trace, trace2])

    for tr in stream:
        response = {"input_units": "counts", "output_units": "cm/s^2"}
        tr.setProvenance("remove_response", response)

    station = StationSummary.from_stream(stream, ["ARITHMETIC_MEAN"], ["duration5-95"])
    pgms = station.pgms
    d595 = pgms.loc["DURATION5-95", "ARITHMETIC_MEAN"].Result

    np.testing.assert_allclose(d595, target_d595, atol=1e-4, rtol=1e-4)

    # Test other components
    data_files, _ = read_data_dir("cwb", "us1000chhc", "2-ECU.dat")
    stream = read_data(data_files[0])[0]
    station = StationSummary.from_stream(
        stream,
        [
            "channels",
            "gmrotd",
            "rotd50",
            "greater_of_two_horizontals",
            "ARITHMETIC_MEAN",
            "geometric_mean",
        ],
        ["duration5-95"],
    )
    # Currently disallowed
    assert "gmrotd" not in station.pgms.index.get_level_values(1)
    assert "rotd50" not in station.pgms.index.get_level_values(1)
    print(station)


def test_duration575():
    datadir = TEST_DATA_DIR / "cosmos" / "us1000hyfh"
    data_file = str(datadir / "us1000hyfh_akbmrp_AKBMR--n.1000hyfh.BNZ.--.acc.V2c")
    stream = read_data(data_file)[0]

    dur = Duration(stream, interval=[5, 75])

    np.testing.assert_allclose(dur.result["HN1"], 45.325, atol=1e-4, rtol=1e-4)


if __name__ == "__main__":
    test_duration()
    test_duration575()


if __name__ == "__main__":
    test_duration()
