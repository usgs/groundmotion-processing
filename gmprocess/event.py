# third party imports
from obspy.core.event.origin import Origin
from obspy.core.event.magnitude import Magnitude
from obspy.core.event.event import Event
from obspy.core.utcdatetime import UTCDateTime
from libcomcat.search import get_event_by_id


def get_event_dict(eventid):
    """Get event dictionary from ComCat using event ID.

    Args:
        eventid (str): Event ID that can be found in ComCat.

    Returns:
        dict: Dictionary containing fields:
            - id String event ID
            - time UTCDateTime of event origin time.
            - lat Origin latitude.
            - lon Origin longitude.
            - depth Origin depth.
            - magnitude Origin magnitude.
    """
    dict_or_id = get_event_by_id(eventid)
    event_dict = {'id': dict_or_id.id,
                  'time': UTCDateTime(dict_or_id.time),
                  'lat': dict_or_id.latitude,
                  'lon': dict_or_id.longitude,
                  'depth': dict_or_id.depth,
                  'magnitude': dict_or_id.magnitude,
                  }
    return event_dict


def get_event_object(dict_or_id):
    """Get Obspy Event object using event ID or dictionary (see get_event_dict).

    Args:
        eventid (dict_or_id): Event ID that can be found in ComCat, or dict.

    Returns:
        Event: Obspy Event object.
    """
    if isinstance(dict_or_id, str):
        event_dict = get_event_dict(dict_or_id)
    elif isinstance(dict_or_id, dict):
        event_dict = dict_or_id.copy()
    else:
        raise Exception('Unknown input parameter to get_event_info()')

    origin = Origin()
    origin.resource_id = event_dict['id']
    origin.latitude = event_dict['lat']
    origin.longitude = event_dict['lon']
    origin.depth = event_dict['depth']

    magnitude = Magnitude(mag=event_dict['magnitude'])
    event = Event()
    event.resource_id = event_dict['id']
    event.origins = [origin]
    event.magnitudes = [magnitude]

    return event
