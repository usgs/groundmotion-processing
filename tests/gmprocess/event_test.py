#!/usr/bin/env python

import os
from gmprocess.event import get_event_dict, get_event_object, ScalarEvent
from obspy.core.event.event import Event
from obspy.core.event.origin import Origin
from obspy.core.event.magnitude import Magnitude
from obspy.core.utcdatetime import UTCDateTime
from obspy.core.event import read_events
import vcr
import pkg_resources


def test_scalar():
    eid = 'usp000hat0'
    time = UTCDateTime('2010-04-06 22:15:01.580')
    lat = 2.383
    lon = 97.048
    depth = 31.0
    mag = 7.8
    mag_type = 'Mwc'

    event = ScalarEvent()
    origin = Origin(resource_id=eid,
                    time=time,
                    latitude=lat,
                    longitude=lon,
                    depth=depth * 1000)
    magnitude = Magnitude(mag=mag, magnitude_type=mag_type)
    event.origins = [origin]
    event.magnitudes = [magnitude]

    assert event.id == eid
    assert event.time == time
    assert event.latitude == lat
    assert event.longitude == lon
    assert event.depth_km == depth
    assert event.magnitude == mag
    assert event.magnitude_type == mag_type

    subdir = os.path.join('data', 'testdata', 'usp000hat0_quakeml.xml')
    quakeml = pkg_resources.resource_filename('gmprocess', subdir)
    catalog = read_events(quakeml)
    tevent = catalog.events[0]
    event = ScalarEvent.fromEvent(tevent)
    assert event.id == 'quakeml:us.anss.org/origin/pde20100406221501580_31'
    assert event.time == time
    assert event.latitude == lat
    assert event.longitude == lon
    assert event.depth_km == depth
    assert event.magnitude == mag
    assert event.magnitude_type == mag_type

    event = ScalarEvent()
    event.fromParams(eid, time, lat, lon, depth, mag, mag_type)
    assert isinstance(event, Event)
    assert event.origins[0].resource_id == eid
    assert event.origins[0].time == time
    assert event.origins[0].latitude == lat
    assert event.origins[0].longitude == lon
    assert event.origins[0].depth == depth * 1000
    assert event.magnitudes[0].mag == mag
    assert event.magnitudes[0].magnitude_type == mag_type

    tevent = Event()
    origin = Origin(resource_id=eid,
                    time=time,
                    longitude=lon,
                    latitude=lat,
                    depth=depth * 1000)
    magnitude = Magnitude(resource_id=eid,
                          mag=mag, magnitude_type=mag_type)
    tevent.origins = [origin]
    tevent.magnitudes = [magnitude]
    event2 = ScalarEvent.fromEvent(tevent)
    assert isinstance(event2, Event)
    assert event2.origins[0].resource_id == eid
    assert event2.origins[0].time == time
    assert event2.origins[0].latitude == lat
    assert event2.origins[0].longitude == lon
    assert event2.origins[0].depth == depth * 1000
    assert event2.magnitudes[0].mag == mag
    assert event2.magnitudes[0].magnitude_type == mag_type


def test_event():
    subdir = os.path.join('data', 'testdata', 'vcr_event_test.yaml')
    tape_file = pkg_resources.resource_filename('gmprocess', subdir)
    with vcr.use_cassette(tape_file):
        eid = 'us1000j96d'  # M7.0 Peru Mar 1 2019
        edict = get_event_dict(eid)
        tdict = {'id': 'us1000j96d',
                 'time': UTCDateTime(2019, 3, 1, 8, 50, 42, 615000),
                 'lat': -14.7007,
                 'lon': -70.1516,
                 'depth': 267,
                 'magnitude': 7.0,
                 'magnitude_type': 'mww'}
        for key, value in tdict.items():
            v1 = edict[key]
            assert value == v1

        event = get_event_object(eid)
        assert event.id == eid
        assert event.magnitude == tdict['magnitude']
        assert event.magnitude_type == tdict['magnitude_type']
        assert event.time == tdict['time']
        assert event.latitude == tdict['lat']
        assert event.longitude == tdict['lon']
        assert event.depth == tdict['depth'] * 1000
        assert event.depth_km == tdict['depth']


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_scalar()
    test_event()
