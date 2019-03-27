#!/usr/bin/env python

import os
from gmprocess.event import get_event_dict, get_event_object
from obspy.core.utcdatetime import UTCDateTime
import vcr


def test_event():
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, '..', 'data')
    tape_file = os.path.join(datadir, 'vcr_event_test.yaml')
    with vcr.use_cassette(tape_file):
        eid = 'us1000j96d'  # M7.0 Peru Mar 1 2019
        edict = get_event_dict(eid)
        tdict = {'id': 'us1000j96d',
                 'time': UTCDateTime(2019, 3, 1, 8, 50, 42, 570000),
                 'lat': -14.7132,
                 'lon': -70.1375,
                 'depth': 267,
                 'magnitude': 7}
        assert edict == tdict

        event = get_event_object(eid)
        assert event.resource_id.id == 'us1000j96d'
        assert event.magnitudes[0].mag == 7.0


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_event()
