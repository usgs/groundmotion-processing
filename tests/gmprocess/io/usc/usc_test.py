#!/usr/bin/env python

# stdlb imports
import os

# third party imports
import numpy as np
import pkg_resources

from gmprocess.io.usc.core import is_usc, read_usc
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.core.stationtrace import PROCESS_LEVELS


def test_usc():
    dpath = os.path.join("data", "testdata", "usc", "ci3144585")
    datadir = pkg_resources.resource_filename("gmprocess", dpath)
    files = {
        "017m30cc.y0a": (-0.049, 0.086),
        "017m30lw.e0a": (0.046, 0.004),
        "017m30lw.e0b": (0.099, 0.004),
        "017m30lw.e0c": (-0.006, 0.025),
        "017m30lw.s0a": (-0.005, 0.014),
        "017m30lw.s0b": (0.066, -0.029),
        "017m30lw.s0c": (-0.026, -0.018),
    }

    streams = []
    for tfilename, accvals in files.items():
        filename = os.path.join(datadir, tfilename)
        assert is_usc(filename)

        # test acceleration from the file
        stream = read_usc(filename)[0]

        # test for one trace per file
        assert stream.count() == 1

        # test that the traces are acceleration
        for trace in stream:
            assert trace.stats.standard.units_type == "acc"
        frac = trace.stats.format_specific.fractional_unit
        # compare the start/end points when converted to gals
        # can't be tested for all due to inconsistent sampling rate
        if tfilename == "017m30cc.y0a":
            np.testing.assert_almost_equal(
                accvals[0] * frac * 980.665, stream[0].data[0]
            )
            np.testing.assert_almost_equal(
                accvals[1] * frac * 980.665, stream[0].data[-1]
            )

        # append to list of streams, so we can make sure these group together
        streams.append(stream)

    # test location override
    stream = read_usc(filename, location="test")[0]
    for trace in stream:
        assert trace.stats.location == "test"

    newstreams = StreamCollection(streams)
    assert len(newstreams) == 3

    meta_stream = read_usc(os.path.join(datadir, "017m30cc.y0a"))[0]
    stats = meta_stream[0].stats
    assert stats["network"] == "LA"
    assert stats["station"] == "57"
    assert stats["channel"] == "HN1"
    assert stats["location"] == "--"
    dt = "%Y-%m-%dT%H:%M:%SZ"
    assert stats["starttime"].strftime(dt) == "1994-01-17T12:30:00Z"
    # assert stats['npts'] == 7340
    np.testing.assert_almost_equal(stats.coordinates["latitude"], 34.419, 3)
    np.testing.assert_almost_equal(stats.coordinates["longitude"], -118.426, 3)
    assert stats.coordinates["elevation"] == 0.0
    assert stats.standard["horizontal_orientation"] == 0
    assert stats.standard["instrument_period"] == 0.039
    assert stats.standard["instrument_damping"] == 0.577
    assert stats.standard["process_time"] == ""
    assert stats.standard["process_level"] == PROCESS_LEVELS["V1"]
    assert (
        stats.standard["station_name"] == "16628 W. LOST CANYON RD., CANYON COUNTRY, CA"
    )
    assert stats.standard["sensor_serial_number"] == ""
    assert stats.standard["instrument"] == ""
    assert stats.standard["comments"] == ""
    assert stats.standard["units_type"] == "acc"
    assert stats.standard["structure_type"] == ""
    assert stats.standard["source_format"] == "usc"
    assert (
        stats.standard["source"]
        == "Los Angeles Basin Seismic Network, University of Southern California"
    )
    assert stats.format_specific["fractional_unit"] == 0.100

    # Verify that the stream was resampled correctly due to uneven spacing
    assert (
        meta_stream[0].getProvenance("resample")[0]["method"]
        == "Linear interpolation of unevenly spaced samples"
    )
    assert stats.sampling_rate == 200

    filename = os.path.join(datadir, "017m30bt.s0a")
    assert is_usc(filename) == True

    # test that volume 2 is not available yet
    try:
        read_usc(filename)[0]
        success = True
    except BaseException:
        success = False
    assert success == False

    # test wrong format exception
    try:
        datadir = os.path.join(homedir, "..", "..", "..", "data", "smc")
        read_usc(os.path.join(datadir, "0111b.smc"))[0]
        success = True
    except Exception:
        success = False
    assert success == False


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_usc()
