#!/usr/bin/env python

# stdlib imports
import os
import tempfile
from datetime import datetime, timedelta
import shutil
import pytest

# third party imports
import numpy as np
from obspy.core.utcdatetime import UTCDateTime

# local imports
from gmprocess.utils.constants import UNIT_CONVERSIONS
from gmprocess.io.dmg.core import is_dmg, read_dmg, _get_date, _get_time
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.core.stationtrace import PROCESS_LEVELS


def test_time():
    line1 = (
        "Uncorrected Accelerogram Data             Processed: 02/13/12, CGS  146be002 "
    )
    line2 = "89146-L2500-12044.02                 Start time:  2/13/12, 21:06:45.0 UTC (GPS)"
    line3 = "JANUARY 17, 1994 04:31 PST              (ORIGIN(CIT): 01/17/94, 12:30:55.4 GMT) "
    date = _get_date(line1)
    assert date == datetime(2012, 2, 13)
    date = _get_date(line2)
    assert date == datetime(2012, 2, 13)
    dt = _get_time(line2)
    assert timedelta(seconds=76005) == dt
    dt = _get_time(line3)
    assert timedelta(seconds=45055, microseconds=399999) == dt
    date = _get_date(line3)
    dtime = date + dt
    assert dtime == datetime(1994, 1, 17, 12, 30, 55, 399999)


def test_dmg_non_spec():
    # where is this script?
    file1, _ = read_data_dir("dmg", "ci3031425", files=["ce23583r_HESPERIA.RAW"])
    file1 = file1[0]
    assert is_dmg(file1)
    stream = read_dmg(file1)[0]
    trace1 = stream[0]
    # Data is in g not gal so it must be scaled by 980.665
    np.testing.assert_almost_equal(trace1.data[0], -0.000116 * UNIT_CONVERSIONS["g"])
    np.testing.assert_almost_equal(trace1.data[-8], -0.003018 * UNIT_CONVERSIONS["g"])


def test_dmg_v1():
    file1, _ = read_data_dir("dmg", "ci3144585", files=["LA116TH.RAW"])
    file1 = file1[0]
    assert is_dmg(file1)

    stream1 = read_dmg(file1)[0]
    assert stream1.count() == 3

    # test that the traces are acceleration
    for trace in stream1:
        assert trace.stats["standard"]["units_type"] == "acc"

    # test metadata
    for trace in stream1:
        stats = trace.stats
        assert stats["station"] == "14403"
        assert stats["delta"] == 0.005
        assert stats["location"] == "--"
        assert stats["network"] == "--"
        dt = "%Y-%m-%dT%H:%M:%SZ"
        assert stats["starttime"].strftime(dt) == "1994-01-17T12:31:04Z"
        assert stats.coordinates["latitude"] == 33.929
        assert stats.coordinates["longitude"] == -118.26
        assert stats.standard["station_name"] == "LOS ANGELES - 116TH ST. SCHOOL"
        assert stats.standard["instrument"] == "SMA-1"
        assert stats.standard["sensor_serial_number"] == "3492"
        if stats["channel"] == "HN1":
            assert stats.format_specific["sensor_sensitivity"] == 1.915
            assert stats.standard["horizontal_orientation"] == 360
            assert stats.standard["instrument_period"] == 0.038
            assert stats.standard["instrument_damping"] == 0.59
            assert stats.format_specific["time_sd"] == 0.115
        if stats["channel"] == "HN2":
            assert stats.standard["horizontal_orientation"] == 90
            assert stats.standard["instrument_period"] == 0.04
            assert stats.standard["instrument_damping"] == 0.592
            assert stats.format_specific["time_sd"] == 0.12
        if stats["channel"] == "HNZ":
            assert stats.standard["horizontal_orientation"] == 0.0
            assert stats.standard["instrument_period"] == 0.039
            assert stats.standard["instrument_damping"] == 0.556
            assert stats.format_specific["time_sd"] == 0.114
        assert stats.standard["process_level"] == PROCESS_LEVELS["V1"]
        assert stats.standard["source_format"] == "dmg"
        assert stats.standard["source"] == "unknown"


def test_dmg():
    file1, _ = read_data_dir("dmg", "nc71734741", files=["CE89146.V2"])
    file2, _ = read_data_dir("dmg", "ci15481673", files=["CIWLT.V2"])
    file3, _ = read_data_dir("dmg", "nc72282711", files=["CE58667.V2"])
    file1 = file1[0]
    file2 = file2[0]
    file3 = file3[0]

    for filename in [file1, file2]:
        assert is_dmg(file1)
        # test acceleration from the file
        stream1 = read_dmg(filename)[0]

        # test for three traces
        assert stream1.count() == 3

        # test that the traces are acceleration
        for trace in stream1:
            assert trace.stats["standard"]["units_type"] == "acc"

    # Test metadata
    stream = read_dmg(file1)[0]
    for trace in stream:
        stats = trace.stats
        assert stats["station"] == "89146"
        assert stats["delta"] == 0.005000
        assert stats["location"] == "--"
        assert stats["network"] == "--"
        dt = "%Y-%m-%dT%H:%M:%SZ"
        assert stats["starttime"].strftime(dt) == "2012-02-13T21:06:45Z"
        assert stats.coordinates["latitude"] == 40.941
        assert stats.coordinates["longitude"] == -123.633
        assert stats.standard["station_name"] == "Willow Creek"
        assert stats.standard["instrument"] == "Etna"
        assert stats.standard["sensor_serial_number"] == "2500"
        if stats["channel"] == "H1":
            assert stats.format_specific["sensor_sensitivity"] == 629
            assert stats.standard["horizontal_orientation"] == 360
            assert stats.standard["instrument_period"] == 0.0108814
            assert stats.standard["instrument_damping"] == 0.6700000
        if stats["channel"] == "H2":
            assert stats.standard["horizontal_orientation"] == 90
            assert stats.standard["instrument_period"] == 0.0100000
            assert stats.standard["instrument_damping"] == 0.6700000
        if stats["channel"] == "Z":
            assert stats.standard["horizontal_orientation"] == 500
            assert stats.standard["instrument_period"] == 0.0102354
            assert stats.standard["instrument_damping"] == 0.6700000
        assert stats.standard["process_level"] == PROCESS_LEVELS["V2"]
        assert stats.standard["source_format"] == "dmg"
        assert stats.standard["source"] == "unknown"
        assert str(stats.format_specific["time_sd"]) == "nan"
        assert stats.format_specific["scaling_factor"] == 980.665
        assert stats.format_specific["low_filter_corner"] == 0.3
        assert stats.format_specific["high_filter_corner"] == 40

    stream = read_dmg(file2)[0]
    for trace in stream:
        stats = trace.stats
        assert stats["station"] == "WLT"
        assert stats["delta"] == 0.0200000
        assert stats["location"] == "--"
        assert stats["network"] == "CI"
        dt = "%Y-%m-%dT%H:%M:%SZ"
        assert stats["starttime"].strftime(dt) == "2014-03-29T04:09:34Z"
        assert stats.coordinates["latitude"] == 34.009
        assert stats.coordinates["longitude"] == -117.951
        assert stats.standard["station_name"] == "Hacienda Heights"
        assert stats.standard["instrument"] == ""
        assert stats.standard["sensor_serial_number"] == "4310"
        assert (
            stats.standard["source"]
            == "Southern California Seismic "
            + "Network, California Institute of Technology (Caltech)"
        )

    # test acceleration from the file
    stream3 = read_dmg(filename)[0]
    assert len(stream3) == 3

    # Test for wrong format exception
    success = True
    try:
        file3, _ = read_data_dir("cwb", "us1000chhc", files=["1-EAS.dat"])
        file3 = file3[0]
        read_dmg(file3)[0]
    except Exception:
        success = False
    assert success == False

    # Test for bad date in header warning
    try:
        file4, _ = read_data_dir("dmg", "nc71734741", files=["BadHeader.V2"])
        file4 = file4[0]
        read_dmg(file4)[0]
    except BaseException:
        success = False
    assert success == False
    # Test alternate defaults
    no_stream = """RESPONSE AND FOURIER AMPLITUDE SPECTRA
    CORRECTED ACCELEROGRAM
    UNCORRECTED ACCELEROGRAM DATA"""

    temp_dir = tempfile.mkdtemp()
    try:
        tmp = os.path.join(temp_dir, "tfile.txt")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(no_stream)
        with pytest.raises(BaseException):
            read_dmg(tmp)[0]
    except Exception as ex:
        raise (ex)
    finally:
        shutil.rmtree(temp_dir)


def test_pacific():
    # test a data file whose trigger time is not in UTC
    file1, _ = read_data_dir("dmg", "nc1091100", files=["ce36456p_CE36456.V2"])
    streams = read_dmg(file1[0])
    trace = streams[0][0]
    # 05/02/83, 16:42:48.2
    cmptime = UTCDateTime("1983-05-02T23:42:48.2")
    assert trace.stats.starttime == cmptime


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_pacific()
    test_dmg_non_spec()
    test_time()
    test_dmg_v1()
    test_dmg()
