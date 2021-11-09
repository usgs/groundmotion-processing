#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import os
import pathlib
from obspy.core.utcdatetime import UTCDateTime

# local imports
from gmprocess.utils.base_utils import read_event_json_files


def test_read_event_json_files():

    thisdir = pathlib.Path(__file__).parent
    datadir = os.path.join(
        thisdir, os.pardir, os.pardir, os.pardir, 'gmprocess', 'data',
        'testdata')
    datafile = os.path.join(datadir, 'event_json', 'event.json')

    eid = 'nc51203888'
    time = UTCDateTime('2008-06-06T09:02:53.890000Z')
    mag = 3.5
    mag_type = 'mw'

    event = read_event_json_files([datafile])[0]
    assert event.id == eid
    assert event.magnitude == mag
    assert event.magnitude_type == mag_type
    assert event.time == time


if __name__ == '__main__':
    test_read_event_json_files()
