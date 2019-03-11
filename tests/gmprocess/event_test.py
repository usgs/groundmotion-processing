#!/usr/bin/env python

from gmprocess.event import get_event_dict, get_event_object
from obspy.core.utcdatetime import UTCDateTime


def test_event():
    eid = 'us1000j96d'  # M7.0 Peru Mar 1 2019
    edict = get_event_dict(eid)
    tdict = {'id': 'us1000j96d',
             'time': UTCDateTime(2019, 3, 1, 8, 50, 41, 530000),
             'lat': -14.6844,
             'lon': -70.1267,
             'depth': 257.42,
             'magnitude': 7}
    assert edict == tdict

    event = get_event_object(eid)
    assert event.resource_id.id == 'us1000j96d'
    assert event.magnitudes[0].mag == 7.0


if __name__ == '__main__':
    test_event()
