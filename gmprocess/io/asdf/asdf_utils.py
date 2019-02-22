# stdlib imports
import json

# third party imports
import numpy as np
from obspy.core.inventory import (Inventory, Network, Station, Response,
                                  Channel, Site, Equipment)

from obspy.core.event.origin import Origin
from obspy.core.event.magnitude import Magnitude
from obspy.core.event.event import Event
from obspy.core.utcdatetime import UTCDateTime
from libcomcat.search import get_event_by_id

UNITS = {'acc': 'cm/s/s',
         'vel': 'cm/s'}
REVERSE_UNITS = {'cm/s/s': 'acc',
                 'cm/s': 'vel'}

# if we find places for these in the standard metadata,
# remove them from this list. Anything here will
# be extracted from the stats standard dictionary,
# combined with the format_specific dictionary,
# serialized to json and stored in the station description.
UNUSED_STANDARD_PARAMS = ['instrument_period',
                          'instrument_damping',
                          'process_time',
                          'process_level',
                          'structure_type',
                          'corner_frequency']


def get_event_info(dict_or_id):
    if isinstance(dict_or_id, str):
        dict_or_id = get_event_by_id(dict_or_id)
        event_dict = {'id': dict_or_id.id,
                      'time': UTCDateTime(dict_or_id.time),
                      'lat': dict_or_id.latitude,
                      'lon': dict_or_id.longitude,
                      'depth': dict_or_id.depth,
                      'magnitude': dict_or_id.magnitude,
                      }
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
    event.origins = [origin]
    event.magnitudes = [magnitude]

    return event


def channel_from_stats(stats):
    units = UNITS[stats.standard.units]
    equipment = Equipment(type=stats.standard.instrument,
                          serial_number=stats.standard.sensor_serial_number)
    depth = 0.0
    azimuth = None
    if not np.isnan(stats.standard.horizontal_orientation):
        azimuth = stats.standard.horizontal_orientation

    response = None
    if 'response' in stats:
        response = stats['response']
    channel = Channel(stats.channel,
                      stats.location,
                      stats.coordinates['latitude'],
                      stats.coordinates['longitude'],
                      stats.coordinates['elevation'],
                      depth,
                      azimuth=azimuth,
                      sample_rate=stats.sampling_rate,
                      storage_format=stats.standard.source_format,
                      calibration_units=units,
                      comments=stats.standard.comments,
                      response=response,
                      sensor=equipment)
    return channel


def stats_from_inventory(inventory):
    channel_stats = {}
    if len(inventory.source):
        source = inventory.source
    station = inventory.networks[0].stations[0]
    coords = {'latitude': station.latitude,
              'longitude': station.longitude,
              'elevation': station.elevation}
    for channel in station.channels:
        stats = {}
        standard = {}
        if channel.sensor.type != 'None':
            standard['instrument'] = channel.sensor.type
        if channel.sensor.serial_number != 'None':
            standard['sensor_serial_number'] = channel.sensor.serial_number
        if channel.azimuth is not None:
            standard['horizontal_orientation'] = channel.azimuth
        standard['source_format'] = channel.storage_format
        standard['units'] = REVERSE_UNITS[channel.calibration_units]
        if len(channel.comments):
            standard['comments'] = channel.comments[0]
        if station.site.name != 'None':
            standard['station_name'] = station.site.name
        # extract the remaining standard info and format_specific info
        # from a JSON string in the station description.
        stats['standard'] = standard
        stats['coordinates'] = coords
        if station.description != 'None':
            jsonstr = station.description
            big_dict = json.loads(jsonstr)
            standard.update(big_dict['standard'])
            format_specific = big_dict['format_specific']
            if len(format_specific):
                stats['format_specific'] = format_specific

        if channel.response is not None:
            stats['response'] = channel.response

        channel_stats[channel.code] = stats

    return channel_stats


def inventory_from_stream(stream):
    """Extract an ObsPy inventory object from a Stream read in by gmprocess tools.

    """
    networks = [trace.stats.network for trace in stream]
    if len(set(networks)) > 1:
        raise Exception("Input stream has stations from multiple networks.")

    # We'll first create all the various objects. These strongly follow the
    # hierarchy of StationXML files.
    source = ''
    if 'standard' in stream[0].stats and 'source' in stream[0].stats.standard:
        source = stream[0].stats.standard.source
    inv = Inventory(
        # We'll add networks later.
        networks=[],
        # The source should be the id whoever create the file.
        source=source)

    net = Network(
        # This is the network code according to the SEED standard.
        code=networks[0],
        # A list of stations. We'll add one later.
        stations=[],
        description="source",
        # Start-and end dates are optional.
    )
    channels = []
    for trace in stream:
        channel = channel_from_stats(trace.stats)
        channels.append(channel)

    subdict = dict((k, stream[0].stats.standard[k])
                   for k in UNUSED_STANDARD_PARAMS)

    format_specific = {}
    if 'format_specific' in stream[0].stats:
        format_specific = stream[0].stats.format_specific

    big_dict = {'standard': subdict,
                'format_specific': format_specific}
    jsonstr = json.dumps(big_dict)
    sta = Station(
        # This is the station code according to the SEED standard.
        code=stream[0].stats.station,
        latitude=stream[0].stats.coordinates.latitude,
        elevation=stream[0].stats.coordinates.elevation,
        longitude=stream[0].stats.coordinates.longitude,
        channels=channels,
        site=Site(name=stream[0].stats.standard.station_name),
        description=jsonstr,
        creation_date=UTCDateTime(1970, 1, 1),  # this is bogus
        total_number_of_channels=len(stream))

    net.stations.append(sta)
    inv.networks.append(net)

    return inv
