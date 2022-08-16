#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
from obspy.core.utcdatetime import UTCDateTime

# local imports
from gmprocess.utils.base_utils import read_event_json_files
from gmprocess.utils.constants import TEST_DATA_DIR


def test_read_event_json_files():

    datafile = TEST_DATA_DIR / "event_json" / "event.json"

    eid = "nc51203888"
    time = UTCDateTime("2008-06-06T09:02:53.890000Z")
    mag = 3.5
    mag_type = "mw"

    event = read_event_json_files([datafile])[0]
    assert event.id == eid
    assert event.magnitude == mag
    assert event.magnitude_type == mag_type
    assert event.time == time


if __name__ == "__main__":
    test_read_event_json_files()
