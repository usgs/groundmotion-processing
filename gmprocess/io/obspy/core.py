#!/usr/bin/env python

# stdlib imports
import os
import sys
import logging
import glob
import re

# third party
from obspy.core.stream import read
from obspy import read_inventory

# local imports
from gmprocess.core.stationtrace import StationTrace
from gmprocess.core.stationstream import StationStream
from gmprocess.utils.config import get_config

IGNORE_FORMATS = ['KNET']
EXCLUDE_PATTERNS = ['*.*.??.LN?']
REQUIRES_XML = ['MSEED']


# Bureau of Reclamation has provided a table of location codes with
# associated descriptions. We are using this primarily to determine whether
# or not the sensor is free field. You may notice that the
# "Down Hole Free Field"
# code we have marked as *not* free field, since borehole sensors do not match
# our definition of "free field".
RE_NETWORK = {
    '10': {
        'description': 'Free field (rock) in vicinity of crest/toe area',
        'free_field': True},
    '11': {
        'description': 'Free field (Left Abutment) either crest or toe',
        'free_field': True},
    '12': {
        'description': 'Free field (Right Abutment) either crest or toe',
        'free_field': True},
    '13': {
        'description': 'Free field (water) (Towards Left Abutment)',
        'free_field': False},
    '14': {
        'description': 'Free field (water) (Towards Right Abutment)',
        'free_field': False},

    '20': {
        'description': 'Toe (center)',
        'free_field': False},
    '21': {
        'description': 'Toe (Left Abutment)',
        'free_field': False},
    '22': {
        'description': 'Toe (Right Abutment)',
        'free_field': False},
    '23': {
        'description': 'Toe (Towards Left Abutment)',
        'free_field': False},
    '24': {
        'description': 'Toe (Towards Right Abutment)',
        'free_field': False},

    '30': {
        'description': 'Crest (center)',
        'free_field': False},
    '31': {
        'description': 'Crest (Left Abutment)',
        'free_field': False},
    '32': {
        'description': 'Crest (Right Abutment)',
        'free_field': False},
    '33': {
        'description': 'Crest (Towards Left Abutment)',
        'free_field': False},
    '34': {
        'description': 'Crest (Towards Right Abutment)',
        'free_field': False},

    '40': {
        'description': 'Foundation (center)',
        'free_field': False},
    '41': {
        'description': 'Foundation (Left Abutment)',
        'free_field': False},
    '42': {
        'description': 'Foundation (Right Abutment)',
        'free_field': False},
    '43': {
        'description': 'Foundation (Towards Left Abutment)',
        'free_field': False},
    '44': {
        'description': 'Foundation (Towards Right Abutment)',
        'free_field': False},

    '50': {
        'description': 'Body (center)',
        'free_field': False},
    '51': {
        'description': 'Body (Left Abutment)',
        'free_field': False},
    '52': {
        'description': 'Body (Right Abutment)',
        'free_field': False},
    '53': {
        'description': 'Body (Towards Left Abutment)',
        'free_field': False},
    '54': {
        'description': 'Body (Towards Right Abutment)',
        'free_field': False},

    '60': {
        'description': 'Down Hole Upper Body',
        'free_field': False},
    '61': {
        'description': 'Down Hole Mid Body',
        'free_field': False},
    '62': {
        'description': 'Down Hole Foundation',
        'free_field': False},
    '63': {
        'description': 'Down Hole Free Field',
        'free_field': False},
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


def is_obspy(filename):
    """Check to see if file is a format supported by Obspy (not KNET).

    Note: Currently only SAC and Miniseed are supported.

    Args:
        filename (str):
            Path to possible Obspy format.
    Returns:
        bool: True if obspy supported, otherwise False.
    """
    logging.debug("Checking if format is supported by obspy.")
    if not os.path.isfile(filename):
        return False
    try:
        stream = read(filename)
        if stream[0].stats._format in IGNORE_FORMATS:
            return False
        if stream[0].stats._format in REQUIRES_XML:
            xmlfile = _get_station_file(filename, stream)
            if not os.path.isfile(xmlfile):
                return False
            return True
        else:
            return True
    except BaseException:
        return False

    return False


def read_obspy(filename, config=None, **kwargs):
    """Read Obspy data file (SAC and MiniSEED currently supported).

    Args:
        filename (str):
            Path to data file.
        config (dict):
            Dictionary containing configuration.
            If None, retrieve global config.
        kwargs (ref):
            Other arguments will be ignored.

    Returns:
        Stream: StationStream object.
    """
    logging.debug("Starting read_obspy.")
    if config is None:
        config = get_config()
    if not is_obspy(filename):
        raise Exception('%s is not a valid Obspy file format.' % filename)

    if 'exclude_patterns' in kwargs:
        exclude_patterns = kwargs.get('exclude_patterns', EXCLUDE_PATTERNS)
    else:
        try:
            fetch_cfg = config['fetchers']
            fdsn_cfg = fetch_cfg['FDSNFetcher']
            if 'exclude_patterns' in fdsn_cfg:
                exclude_patterns = fdsn_cfg['exclude_patterns']
        except BaseException:
            exclude_patterns = EXCLUDE_PATTERNS

    streams = []
    tstream = read(filename)
    try:
        xmlfile = _get_station_file(filename, tstream)
        inventory = read_inventory(xmlfile)
    except BaseException:
        inventory = None
    traces = []

    for ttrace in tstream:
        trace = StationTrace(
            data=ttrace.data,
            header=ttrace.stats,
            inventory=inventory,
            config=config)
        network = ttrace.stats.network
        station = ttrace.stats.station
        channel = ttrace.stats.channel

        if ttrace.stats.location == '':
            ttrace.stats.location = '--'
        location = ttrace.stats.location

        # full instrument name for matching purposes
        instrument = '%s.%s.%s.%s' % (network, station,
                                      location, channel)

        # Search for a match using regular expressions.
        for pattern in exclude_patterns:

            # Split each string into components. Check if
            # components are of equal length.
            pparts = pattern.split('.')
            instparts = instrument.split('.')
            if len(pparts) != len(instparts):
                logging.info('There are too many fields in the '
                             'exclude_pattern element. Ensure '
                             'that you have 4 fields: Network, '
                             'Station ID, Location Code, and Channel.')
                sys.exit(0)
            # Loop over each component, convert the pattern's field
            # into its regular expression form, and see if the
            # pattern is in the instrument's component.
            no_match = False
            for pat, instfield in zip(pparts, instparts):
                pat = pat.replace('*', '.*').replace('?', '.')
                if re.search(pat, instfield) is None:
                    no_match = True
                    break
            if no_match:
                continue
            else:
                logging.info(
                    '%s is an instrument that should be excluded. '
                    'The station is not going into the station stream.'
                    % instrument)
                break

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
    if no_match is True:
        stream = StationStream(traces=traces)
        streams.append(stream)

        return streams
