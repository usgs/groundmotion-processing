#!/usr/bin/env python

# stdlib imports
import os
import logging
import glob

# third party
from obspy.core.stream import read
from obspy import read_inventory

# local imports
from gmprocess.stationtrace import StationTrace
from gmprocess.stationstream import StationStream
from gmprocess.io.seedname import get_channel_name, is_channel_north
from gmprocess.config import get_config

IGNORE_FORMATS = ['KNET']
EXCLUDE_BANDS = ['L']

# Bureau of Reclamation has provided a table of location codes with
# associated descriptions. We are using this primarily to determine whether
# or not the sensor is free field. You may notice that the
# "Down Hole Free Field"
# code we have marked as *not* free field, since borehole sensors do not match
# our definition of "free field".
RE_NETWORK = {
    '10': {'description': 'Free field (rock) in vicinity of crest/toe area', 'free_field': True},
    '11': {'description': 'Free field (Left Abutment) either crest or toe', 'free_field': True},
    '12': {'description': 'Free field (Right Abutment) either crest or toe', 'free_field': True},
    '13': {'description': 'Free field (water) (Towards Left Abutment)', 'free_field': False},
    '14': {'description': 'Free field (water) (Towards Right Abutment)', 'free_field': False},

    '20': {'description': 'Toe (center)', 'free_field': False},
    '21': {'description': 'Toe (Left Abutment)', 'free_field': False},
    '22': {'description': 'Toe (Right Abutment)', 'free_field': False},
    '23': {'description': 'Toe (Towards Left Abutment)', 'free_field': False},
    '24': {'description': 'Toe (Towards Right Abutment)', 'free_field': False},

    '30': {'description': 'Crest (center)', 'free_field': False},
    '31': {'description': 'Crest (Left Abutment)', 'free_field': False},
    '32': {'description': 'Crest (Right Abutment)', 'free_field': False},
    '33': {'description': 'Crest (Towards Left Abutment)', 'free_field': False},
    '34': {'description': 'Crest (Towards Right Abutment)', 'free_field': False},

    '40': {'description': 'Foundation (center)', 'free_field': False},
    '41': {'description': 'Foundation (Left Abutment)', 'free_field': False},
    '42': {'description': 'Foundation (Right Abutment)', 'free_field': False},
    '43': {'description': 'Foundation (Towards Left Abutment)', 'free_field': False},
    '44': {'description': 'Foundation (Towards Right Abutment)', 'free_field': False},

    '50': {'description': 'Body (center)', 'free_field': False},
    '51': {'description': 'Body (Left Abutment)', 'free_field': False},
    '52': {'description': 'Body (Right Abutment)', 'free_field': False},
    '53': {'description': 'Body (Towards Left Abutment)', 'free_field': False},
    '54': {'description': 'Body (Towards Right Abutment)', 'free_field': False},

    '60': {'description': 'Down Hole Upper Body', 'free_field': False},
    '61': {'description': 'Down Hole Mid Body', 'free_field': False},
    '62': {'description': 'Down Hole Foundation', 'free_field': False},
    '63': {'description': 'Down Hole Free Field', 'free_field': False},
}

LOCATION_CODES = {'RE': RE_NETWORK}


def _get_station_file(filename, stream):
    filebase, fname = os.path.split(filename)
    network = stream[0].stats.network
    station = stream[0].stats.station
    pattern = '%s.%s.xml' % (network, station)
    xmlfiles = glob.glob(os.path.join(filebase, pattern))
    if len(xmlfiles) != 1:
        return 'None'
    xmlfile = xmlfiles[0]
    return xmlfile


def is_fdsn(filename):
    """Check to see if file is a format supported by Obspy (not KNET).

    Args:
        filename (str): Path to possible Obspy format.
    Returns:
        bool: True if obspy supported, otherwise False.
    """
    logging.debug("Checking if format is Obspy.")
    if not os.path.isfile(filename):
        return False
    try:
        stream = read(filename)
        if stream[0].stats._format in IGNORE_FORMATS:
            return False
        xmlfile = _get_station_file(filename, stream)
        if not os.path.isfile(xmlfile):
            return False
        return True
    except Exception:
        return False

    return False


def read_fdsn(filename):
    """Read Obspy data file (SAC, MiniSEED, etc).

    Args:
        filename (str):
            Path to data file.
        kwargs (ref):
            Other arguments will be ignored.
    Returns:
        Stream: StationStream object.
    """
    print('I AM IN READ_FDSN!!!!!!!')
    logging.debug("Starting read_fdsn.")
    if not is_fdsn(filename):
        raise Exception('%s is not a valid Obspy file format.' % filename)

    exclude_bands = EXCLUDE_BANDS
    if 'fetchers' in config:
        if 'FDSNFetcher' in config['fetchers']:
            fetch_cfg = config['fetchers']['FDSNFetcher']
            if 'exclude_bands' in fetch_cfg:
                exclude_bands = fetch_cfg['exclude_bands']

    streams = []
    tstream = read(filename)
    xmlfile = _get_station_file(filename, tstream)
    inventory = read_inventory(xmlfile)
    traces = []
    for ttrace in tstream:
        trace = StationTrace(data=ttrace.data,
                             header=ttrace.stats,
                             inventory=inventory)
        location = ttrace.stats.location

        #channel = ttrace.stats.channel
        #band  = channel[0]
        #print(band)
        #if band in exclude_bands:
        #    logging.info('%s has a band which should be excluded.'
        #                 'Not reading in %s into stream.' % ttrace)
        #    break

        if trace.stats.location == '':
            trace.stats.location = '--'

        network = ttrace.stats.network
        if network in LOCATION_CODES:
            codes = LOCATION_CODES[network]
            if location in codes:
                sdict = codes[location]
                if sdict['free_field']:
                    trace.stats.standard.structure_type = 'free_field'
                else:
                    trace.stats.standard.structure_type = sdict['description']
        head, tail = os.path.split(filename)
        trace.stats['standard']['source_file'] = tail or os.path.basename(head)
        traces.append(trace)
    stream = StationStream(traces=traces)
    streams.append(stream)

    return streams
