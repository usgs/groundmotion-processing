#!/usr/bin/env python

import logging
import numpy as np
from gmprocess.io.seedname import get_channel_name
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from obspy.core.util.attribdict import AttribDict

from gmprocess.config import get_config


CONFIG = get_config()
TIMEFMT = '%Y-%m-%dT%H:%M:%S'


def request_raw_waveforms(
        fdsn_client=None,
        org_time=None,
        lat=None,
        lon=None,
        before_time=None,
        after_time=None,
        dist_min=None,
        dist_max=None,
        networks=None,
        stations=None,
        channels=None):
    """
    Requests raw waveform data from an FDSN client.
    The requested data can be constrained by time, distance from event,
    network, station, and channels.

    Args:
        fdsn_client (str):
            A string for the FDSN client. Valid choices are:
                BGR, EMSC, ETH, GEONET, GFZ, ICGC, INGV, IPGP, IRIS, ISC,
                KOERI, LMU, NCEDC, NIEP, NOA, ODC, ORFEUS, RESIF, SCEDC,
                TEXTNET, USGS, and USP
        org_time (str):
            Origin time of event. Must be able to convert to UTCDateTime.
        lat (float):
            Event latitude.
        lon (float):
            Event longitude.
        before_time (int):
            Number of seconds before origin time to request. Default is 120.
        after_time (int):
            Number of seconds after origin time to request. Default is 600.
        dist_min (float):
            Minimum distance (dd) from event epicenter. Default is 0.
        dist_max (float):
            Maximum distance (dd) from event epicenter. Default is 0.1.
        network (list):
            List of strings for desired networks. Default is ['*'].
        channels (list):
            List of strings for desired channels. Default is ['*'].

    Returns:
        stream (obspy.core.trace.Trace): Stream of requested, raw data.
        inventory (obspy.core.inventory): Inventory object for the event.
    """

    # If request options are None, use valeus in config file. This allows
    # for the method to be used as a library or set through the config.
    if before_time is None:
        before_time = CONFIG['waveform_request']['before_time']
    if after_time is None:
        after_time = CONFIG['waveform_request']['after_time']
    if dist_min is None:
        dist_min = CONFIG['waveform_request']['dist_min']
    if dist_max is None:
        dist_max = CONFIG['waveform_request']['dist_max']
    if networks is None:
        networks = CONFIG['waveform_request']['networks']
    if stations is None:
        stations = CONFIG['waveform_request']['stations']
    if channels is None:
        channels = CONFIG['waveform_request']['channels']

    logging.debug('fdsn_client: %s' % fdsn_client)
    client = Client(fdsn_client)

    # Time information
    origin_time = UTCDateTime(org_time)
    t1 = origin_time - before_time
    t2 = origin_time + after_time
    logging.debug('t1: %s' % t1)
    logging.debug('t2: %s' % t2)

    # Convert lists to comma-separated strings
    networks = ','.join(networks)
    stations = ','.join(stations)
    channels = ','.join(channels)
    logging.debug('networks: %s' % networks)
    logging.debug('stations: %s' % stations)
    logging.debug('channels: %s' % channels)

    # Get an inventory of all stations for the event
    inventory = client.get_stations(
        starttime=t1,
        endtime=t2,
        latitude=lat,
        longitude=lon,
        minradius=dist_min,
        maxradius=dist_max,
        network=networks,
        channel=channels,
        station=stations,
        level='response',
        includerestricted=False)

    # Get the list of channels from the inventory
    channels = inventory.get_contents()['channels']
    logging.info('Found {0} channels.'.format(len(channels)))

    # Set up the bulk data for the bulk data request
    bulk = [chan.split('.') for chan in channels]
    for b in bulk:
        b.append(t1)
        b.append(t2)

    # Perform the bulk data request
    logging.info(
        'Requesting waveforms for {0} channels.'.format(len(channels)))
    st = client.get_waveforms_bulk(bulk, attach_response=True)
    return st, inventory


def add_channel_metadata(tr, inv, client):
    """
    Adds the channel metadata for each channel in the stream.

    Args:
        tr (obspy.core.trace.Trace):
            Trace of requested data.
        inv (obspy.core.inventory):
            Inventory object corresponding to to the stream.
        client (str):
            FDSN client indicator.

    Returns:
        trace (obspy.core.trace.Trace): Trace with metadata added.
    """

    time = tr.stats.starttime
    id_string = tr.stats.network + '.' + tr.stats.station + '.'
    id_string += tr.stats.location + '.' + tr.stats.channel
    if tr.stats.location == '':
        tr.stats.location = '--'
    metadata = inv.get_channel_metadata(id_string, time)

    coordinates = {
        'latitude': metadata['latitude'],
        'longitude': metadata['longitude'],
        'elevation': metadata['elevation']
    }

    standard = {
        'horizontal_orientation': metadata['azimuth'],
        'instrument_period': np.nan,
        'instrument_damping': np.nan,
        'process_level': 'V0',
        'station_name': tr.stats.station,
        'sensor_serial_number': '',
        'instrument': '',
        'comments': '',
        'structure_type': '',
        'corner_frequency': np.nan,
        'units': 'raw',
        'source': client,
        'source_format': 'fdsn'
    }

    tr.stats['coordinates'] = coordinates
    tr.stats['standard'] = standard

    if metadata['dip'] in [90, -90, 180, -180]:
        tr.stats['channel'] = get_channel_name(
            tr.stats['sampling_rate'],
            is_acceleration=True,
            is_vertical=True,
            is_north=False)
    else:
        ho = metadata['azimuth']
        quad1 = ho > 315 and ho <= 360
        quad2 = ho >= 0 and ho <= 45
        quad3 = ho > 135 and ho <= 225
        if quad1 or quad2 or quad3:
            tr.stats['channel'] = get_channel_name(
                tr.stats['sampling_rate'],
                is_acceleration=True,
                is_vertical=False,
                is_north=True)
        else:
            tr.stats['channel'] = get_channel_name(
                tr.stats['sampling_rate'],
                is_acceleration=True,
                is_vertical=False,
                is_north=False)
    return tr


def clean_stats(my_stats):
    """
    Function for making dictionary json serializable.

    Args:
        stats (dict): Dictionary of stats.

    Returns:
        dictionary: Dictionary of cleaned stats.
    """
    stats = dict()
    for key, value in my_stats.items():
        stats[key] = value

    if 'response' in stats:
        stats['response'] = ''

    for key, value in stats.items():
        if isinstance(value, (dict, AttribDict)):
            stats[key] = dict(clean_stats(value))
        elif isinstance(value, UTCDateTime):
            stats[key] = value.strftime(TIMEFMT)
        elif isinstance(value, float) and np.isnan(value) or value == '':
            stats[key] = 'null'
    return stats
