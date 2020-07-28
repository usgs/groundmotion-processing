#!/usr/bin/env python

# stdlib imports
import os
import logging
import glob
import re

# third party
from obspy.core.stream import read
from obspy import read_inventory

# local imports
from gmprocess.stationtrace import StationTrace
from gmprocess.stationstream import StationStream
from gmprocess.io.seedname import get_channel_name, is_channel_north

IGNORE_FORMATS = ['KNET']


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


def read_fdsn(filename, exclude_seismometers):
    """Read Obspy data file (SAC, MiniSEED, etc).

    Args:
        filename (str):
            Path to data file.
        kwargs (ref):
            Other arguments will be ignored.
    Returns:
        Stream: StationStream object.
    """
    logging.debug("Starting read_fdsn.")
    if not is_fdsn(filename):
        raise Exception('%s is not a valid Obspy file format.' % filename)
 
    streams = []
    tstream = read(filename)
    xmlfile = _get_station_file(filename, tstream)
    inventory = read_inventory(xmlfile)
    traces = []
    for ttrace in tstream:
        not_excluded = True
        trace = StationTrace(data=ttrace.data,
                             header=ttrace.stats,
                             inventory=inventory)
        network = ttrace.stats.network
        station = ttrace.stats.station
        channel = ttrace.stats.channel

        if ttrace.stats.location == '':
            ttrace.stats.location = '--'
        location = ttrace.stats.location

        #full instrument name for matching purposes
        seismo = '%s.%s.%s.%s' % (network, station,
                                  location, channel) 

        #Search for a match using regular expressions.
        for seismo_id in exclude_seismometers:
            #Convert '?' wildcard into regular expression equivalent.
            seismo_re = seismo_id.replace('.', '\.').replace('?', '.')
            #Convert '*' wildcard into regular expression equivalent. 
            #
            #See if there are '*' in the exclusion list. If so, we will 
            #find if the asterik is in the first position, meaning that 
            #we will be not attempting to match a specific network. 
            #
            #
            #If '*' is not in the first position but in the string, then we know
            #that it appears in the station section of the string only.
            if '*' in seismo_re:
                ast_idx = seismo_re.find('*')
                if ast_idx == 0:
                    net_string_re = ''
                    for character in network:
                        net_string_re += '.'
                    seismo_re = seismo_re.replace('*',
                                                    net_string_re,
                                                    1)
                #We must look to see if there is still an '*' in the station
                #portion of the string since we could have entires such as 
                #'*.1234' where we do not want to repalce specific characters
                #with '.' since they are not treated similarly as regular 
                #expressions.
                if '*' in seismo_re:
                    sta_string_re = ''
                    for character in station:
                        sta_string_re += '.'
                    seismo_re = seismo_re.replace('*', sta_string_re)
                else:
                    pass

            #Change channel orientation (if explicitly defined) to a set that includes
            #the channel's alphabetical and numerical forms. 
            last_character = seismo_re[len(seismo_re) - 1]
            if last_character in ['E', 'N', '1', '2']:
                if last_character in ['E', '1']:
                    seismo_re = seismo_re.replace(last_character, '[E1]')
                elif last_character in ['N', '2']:
                    seismo_re = seismo_re.replace(last_character, '[N2]')
            #seek a match. If there is a match, then we do not read in the trace
            #into the StationStream. Else, it will be read in.
            seek_match = re.match(seismo_re, seismo)
            if seek_match != None:
                logging.info('%s.%s.%s.%s is an instrument that should be excluded. '
                             'The station is not going into the station stream.' 
                             % (network, station, location, channel))
                not_excluded = False
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
    if not_excluded == True:
        stream = StationStream(traces=traces)
        streams.append(stream)

        return streams
