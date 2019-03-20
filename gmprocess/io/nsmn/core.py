#!/usr/bin/env python

# stdlib imports
from datetime import datetime
import re
import copy

# third party imports
import numpy as np
from scipy import constants
from obspy.core.utcdatetime import UTCDateTime

# local
from gmprocess.stationstream import StationStream
from gmprocess.stationtrace import StationTrace, PROCESS_LEVELS
from gmprocess.io.seedname import get_channel_name


TIMEFMT = '%d/%m/%Y %H:%M:%S.%f'
FLOATRE = "[-+]?[0-9]*\.?[0-9]+"
INTRE = "[-+]?[0-9]*"

# 20/07/2017 22:30:58.000000
TIME_RE = '[0-9]{2}/[0-9]{2}/[0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}\.?[0-9]*'

TEXT_HDR_ROWS = 18

COLWIDTH = 12
NCOLS = 3

SOURCE = 'National Strong-Motion Network of Turkey (TR-NSMN)'
SOURCE_FORMAT = 'NSMN'
NETWORK = 'TK'

LEVELS = {'VOL1DS': 'V1'}

DECIG_TO_GALS = (constants.g * 100) / 10

MARKER = 'STRONG GROUND MOTION RECORDS OF TURKIYE'

ENCODING = 'ISO-8859-1'
# ENCODING = 'utf-16-be'


def is_nsmn(filename):
    with open(filename, 'rt', encoding=ENCODING) as f:
        line = f.readline()
        if MARKER in line:
            return True

    return False


def read_nsmn(filename):
    """Read the Turkish NSMN strong motion data format.

    Args:
        filename (str): path to NSMN data file.

    Returns:
        list: Sequence of one StationStream object containing 3 StationTrace objects.
    """
    header = _read_header(filename)
    header1 = copy.deepcopy(header)
    header2 = copy.deepcopy(header)
    header3 = copy.deepcopy(header)
    header1['standard']['horizontal_orientation'] = 0.0
    header1['channel'] = get_channel_name(header['sampling_rate'],
                                          True,
                                          False,
                                          True)
    header2['standard']['horizontal_orientation'] = 90.0
    header2['channel'] = get_channel_name(header['sampling_rate'],
                                          True,
                                          False,
                                          False)
    header3['standard']['horizontal_orientation'] = 0.0
    header3['channel'] = get_channel_name(header['sampling_rate'],
                                          True,
                                          True,
                                          False)
    # three columns of NS, EW, UD
    # data = np.genfromtxt(filename, skip_header=TEXT_HDR_ROWS,
    #                      delimiter=[COLWIDTH] * NCOLS, encoding=ENCODING)
    data = np.loadtxt(filename,
                      skiprows=TEXT_HDR_ROWS,
                      encoding=ENCODING)
    data1 = data[:, 0]
    data2 = data[:, 1]
    data3 = data[:, 2]
    trace1 = StationTrace(data=data1, header=header1)
    trace2 = StationTrace(data=data2, header=header2)
    trace3 = StationTrace(data=data3, header=header3)
    stream = StationStream(traces=[trace1, trace2, trace3])
    return [stream]


def _read_header(filename):
    header = {}
    standard = {}
    coords = {}
    format_specific = {}
    with open(filename, 'rt', encoding=ENCODING) as f:
        lines = [next(f) for x in range(TEXT_HDR_ROWS)]
        # fill out the standard dictionary
        standard['source'] = SOURCE
        standard['source_format'] = SOURCE_FORMAT
        standard['instrument'] = lines[9].split(':')[1].strip()
        standard['sensor_serial_number'] = lines[10].split(':')[1].strip()
        standard['process_level'] = PROCESS_LEVELS['V1']
        standard['process_time'] = ''
        standard['station_name'] = lines[1].split(':')[1].strip()
        standard['structure_type'] = ''
        standard['corner_frequency'] = np.nan
        standard['units'] = 'acc'
        standard['instrument_period'] = np.nan
        standard['instrument_damping'] = np.nan
        standard['horizontal_orientation'] = np.nan
        standard['comments'] = ' '.join(lines[15:17]).replace('\n', '')

        # fill out the stats stuff
        stimestr = re.search(TIME_RE, lines[11]).group()
        # 20/07/2017 22:30:58.000000 (GMT)
        stime = datetime.strptime(stimestr, TIMEFMT)
        header['starttime'] = stime
        header['npts'] = int(lines[12].split(':')[1].strip())
        header['delta'] = float(lines[13].split(':')[1].strip())
        header['sampling_rate'] = 1 / header['delta']
        header['duration'] = header['npts'] * header['delta']
        header['channel'] = ''
        header['station'] = lines[6].split(':')[1].strip()
        header['location'] = '--'
        header['network'] = NETWORK

        coordstr = lines[7].split(':')[1].replace('-', '')
        lat_str, lon_str = re.findall(FLOATRE, coordstr)
        altitude = float(lines[8].split(':')[1].strip())
        coords = {'latitude': float(lat_str),
                  'longitude': float(lon_str),
                  'elevation': altitude}

        header['coordinates'] = coords
        header['standard'] = standard
        header['format_specific'] = format_specific

        return header


def _read_header_lines(filename, offset):
    """Read the header lines for each channel.

    Args:
        filename (str): 
            Input BHRC file name.
        offset (int): 
            Number of lines to skip from the beginning of the file.

    Returns:
        tuple: (header dictionary containing Stats dictionary with extra sub-dicts, 
                updated offset rows)
    """
    with open(filename, 'rt') as f:
        for _ in range(offset):
            next(f)
        lines = [next(f) for x in range(TEXT_HDR_ROWS)]

    offset += TEXT_HDR_ROWS

    header = {}
    standard = {}
    coords = {}
    format_specific = {}

    # get the sensor azimuth with respect to the earthquake
    # this data has been rotated so that the longitudinal channel (L)
    # is oriented at the sensor azimuth, and the transverse (T) is
    # 90 degrees off from that.
    station_info = lines[7][lines[7].index('Station'):]
    (lat_str, lon_str,
     alt_str, lstr, tstr) = re.findall(FLOATRE, station_info)
    component = lines[4].strip()
    if component == 'V':
        angle = np.nan
    elif component == 'L':
        angle = float(lstr)
    else:
        angle = float(tstr)
    coords = {'latitude': float(lat_str),
              'longitude': float(lon_str),
              'elevation': float(alt_str)}

    # fill out the standard dictionary
    standard['source'] = SOURCE
    standard['source_format'] = SOURCE_FORMAT
    standard['instrument'] = lines[1].split('=')[1].strip()
    standard['sensor_serial_number'] = ''
    volstr = lines[0].split()[1].strip()
    if volstr not in LEVELS:
        raise KeyError('Volume %s files are not supported.' % volstr)
    standard['process_level'] = PROCESS_LEVELS[LEVELS[volstr]]
    standard['process_time'] = ''
    station_name = lines[7][0:lines[7].index('Station')].strip()
    standard['station_name'] = station_name
    standard['structure_type'] = ''
    standard['corner_frequency'] = np.nan
    standard['units'] = 'acc'
    period_str, damping_str = re.findall(FLOATRE, lines[9])
    standard['instrument_period'] = float(period_str)
    standard['instrument_damping'] = float(damping_str)
    standard['horizontal_orientation'] = angle
    standard['comments'] = ''

    # fill out the stats stuff
    # we don't know the start of the trace
    header['starttime'] = UTCDateTime(1970, 1, 1)
    npts_str, dur_str = re.findall(FLOATRE, lines[10])
    header['npts'] = int(npts_str)
    header['duration'] = float(dur_str)
    header['delta'] = header['duration'] / (header['npts'] - 1)
    header['sampling_rate'] = 1 / header['delta']
    if np.isnan(angle):
        header['channel'] = get_channel_name(
            header['sampling_rate'],
            is_acceleration=True,
            is_vertical=True,
            is_north=False)
    elif (angle > 315 or angle < 45) or (angle > 135 and angle < 225):
        header['channel'] = get_channel_name(
            header['sampling_rate'],
            is_acceleration=True,
            is_vertical=False,
            is_north=True)
    else:
        header['channel'] = get_channel_name(
            header['sampling_rate'],
            is_acceleration=True,
            is_vertical=False,
            is_north=False)

    part1 = lines[0].split(':')[1]
    stationcode = part1.split('/')[0].strip()
    header['station'] = stationcode
    header['location'] = '--'
    header['network'] = NETWORK

    header['coordinates'] = coords
    header['standard'] = standard
    header['format_specific'] = format_specific

    offset += INT_HDR_ROWS
    offset += FLOAT_HDR_ROWS

    return (header, offset)


def _read_data(filename, offset, header):
    """Read acceleration data from BHRC file.

    Args:
        filename (str): 
            BHRC strong motion filename.
        offset (int):
            Number of rows from the beginning of the file to skip.
        header (dict):
            Dictionary for given channel with number of points.

    Returns:
        tuple: (Acceleration data (in gals), updated offset)
    """
    widths = [COLWIDTH] * COLS_PER_ROW
    npoints = header['npts']
    nrows = int(np.ceil(npoints / COLS_PER_ROW))
    data = np.genfromtxt(filename, skip_header=offset,
                         max_rows=nrows, filling_values=np.nan,
                         delimiter=widths)
    data = data.flatten()
    data = data[0:header['npts']]

    # convert data to cm/s^2
    data *= DECIG_TO_GALS

    offset += nrows + 1  # there is an end of record marker line
    return (data, offset)
