#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from json.decoder import JSONDecodeError

from gmprocess.utils.download_utils import get_event_data

# from libcomcat.search import get_event_by_id
from obspy.core.event.event import Event
from obspy.core.event.magnitude import Magnitude

# third party imports
from obspy.core.event.origin import Origin
from obspy.core.utcdatetime import UTCDateTime


class ScalarEvent(Event):
    """Class to represent a flattened Event with only 1 origin and 1 magnitude."""

    def __init__(self, *args, **kwargs):
        super(ScalarEvent, self).__init__(*args, **kwargs)

    @classmethod
    def fromEvent(cls, event):
        eventobj = cls()

        # copy the arrays
        for origin in event.origins:
            eventobj.origins.append(origin.copy())
        #            oldid = eventobj.origins[-1].resource_id.id
        #            eventobj.origins[-1].resource_id.id = oldid.replace(
        #                'smi:local/', '')
        for magnitude in event.magnitudes:
            eventobj.magnitudes.append(magnitude.copy())
        for station_magnitude in event.station_magnitudes:
            eventobj.station_magnitudes.append(station_magnitude.copy())
        for focal_mechanism in event.focal_mechanisms:
            eventobj.focal_mechanisms.append(focal_mechanism.copy())
        for amplitude in event.amplitudes:
            eventobj.amplitudes.append(amplitude.copy())
        for pick in event.picks:
            eventobj.picks.append(pick.copy())
        for comment in event.comments:
            eventobj.comments.append(comment.copy())
        for event_description in event.event_descriptions:
            eventobj.event_descriptions.append(event_description.copy())

        # copy the scalar stuff
        if event.creation_info is not None:
            eventobj.creation_info = event.creation_info.copy()
        if event.resource_id is not None:
            eventobj.resource_id = event.resource_id.copy()
        eventobj.event_type = event.event_type
        eventobj.event_type_certainty = event.event_type_certainty

        return eventobj

    def fromParams(self, id, time, lat, lon, depth, magnitude, mag_type=None):
        """Create a ScalarEvent (subclass of Event).

        Args:
            id (str):
                Desired ID for the event, usually ComCat ID.
            time (UTCDateTime):
                Origin time of the event.
            lat (float):
                Latitude of origin.
            lon (float):
                Longitude of origin.
            depth (float):
                Depth of origin in **kilometers**.
            magnitude (float):
                Magnitude of earthquake.
            mag_type (str):
                Magnitude type of earthqake.
        """
        if isinstance(time, str):
            try:
                time = UTCDateTime(time)
            except BaseException as e:
                fmt = 'Can\'t make UTCDateTime from string "%s" - error "%s"'
                raise TypeError(fmt % (time, str(e)))

        origin = Origin(
            resource_id=id, time=time, longitude=lon, latitude=lat, depth=depth * 1000
        )

        self.origins = [origin]
        magnitude = Magnitude(resource_id=id, mag=magnitude, magnitude_type=mag_type)
        self.magnitudes = [magnitude]
        self.resource_id = id

    def __repr__(self):
        if not hasattr(self, "origins") or not hasattr(self, "magnitudes"):
            return "Empty ScalarEvent"
        fmt = "%s %s %.3f %.3f %.1fkm M%.1f %s"
        tpl = (
            self.id,
            str(self.time),
            self.latitude,
            self.longitude,
            self.depth_km,
            self.magnitude,
            self.magnitude_type,
        )
        return fmt % tpl

    def _get_origin(self):
        origin = self.preferred_origin()
        if origin is None:
            origin = self.origins[0]
        return origin

    def _get_magnitude(self):
        magnitude = self.preferred_magnitude()
        if magnitude is None:
            magnitude = self.magnitudes[0]
        return magnitude

    @property
    def id(self):
        """Return the origin resource_id."""
        origin = self._get_origin()
        return origin.resource_id.id

    @property
    def time(self):
        """Return the origin time."""
        origin = self._get_origin()
        return origin.time

    @property
    def latitude(self):
        """Return the origin latitude."""
        origin = self._get_origin()
        return origin.latitude

    @property
    def longitude(self):
        """Return the origin longitude."""
        origin = self._get_origin()
        return origin.longitude

    @property
    def depth(self):
        """Return the origin depth."""
        origin = self._get_origin()
        return origin.depth

    @property
    def depth_km(self):
        """Return the origin depth."""
        origin = self._get_origin()
        return origin.depth / 1000

    @property
    def magnitude(self):
        """Return the magnitude value."""
        magnitude = self._get_magnitude()
        return magnitude.mag

    @property
    def magnitude_type(self):
        """Return the magnitude type."""
        return self.magnitudes[0]["magnitude_type"]


def get_event_dict(eventid):
    """Get event dictionary from ComCat using event ID.

    Args:
        eventid (str):
            Event ID that can be found in ComCat.

    Returns:
        dict: Dictionary containing fields:
            - id String event ID
            - time UTCDateTime of event origin time.
            - lat Origin latitude.
            - lon Origin longitude.
            - depth Origin depth.
            - magnitude Origin magnitude.
    """
    event_data = get_event_data(eventid)
    if event_data["id"] != eventid:
        logging.warn(
            "Event ID %s is no longer preferred. Updating with the "
            "preferred event ID: %s." % (eventid, event_data["id"])
        )
    event_dict = {
        "id": event_data["id"],
        "time": UTCDateTime(event_data["properties"]["time"] / 1000),
        "lat": event_data["geometry"]["coordinates"][1],
        "lon": event_data["geometry"]["coordinates"][0],
        "depth": event_data["geometry"]["coordinates"][2] / 1000,
        "magnitude": event_data["properties"]["mag"],
        "magnitude_type": event_data["properties"]["magType"],
    }
    return event_dict


def get_event_object(dict_or_id):
    """Get ScalarEvent object using event ID or dictionary
    (see get_event_dict).

    Args:
        eventid (dict_or_id):
            Event ID that can be found in ComCat, or dict.

    Returns:
        Event: Obspy Event object.
    """
    if isinstance(dict_or_id, str):
        try:
            event_dict = get_event_dict(dict_or_id)
        except JSONDecodeError as e:
            logging.info(
                "JSONDecodeError error encountered while retrieving event "
                f"info for {dict_or_id}:"
            )
            logging.info(f"Error: {e}")
            return None
    elif isinstance(dict_or_id, dict):
        event_dict = dict_or_id.copy()
    else:
        raise Exception("Unknown input parameter to get_event_info()")
    event = ScalarEvent()
    if "magnitude_type" not in event_dict.keys():
        event_dict["magnitude_type"] = None
    event.fromParams(
        event_dict["id"],
        event_dict["time"],
        event_dict["lat"],
        event_dict["lon"],
        event_dict["depth"],
        event_dict["magnitude"],
        event_dict["magnitude_type"],
    )
    return event
