#!/usr/bin/env python

# stdlib imports
from datetime import datetime
import re
import logging

# third party
from obspy.core.trace import Stats
import numpy as np

# local imports
from gmprocess.io.seedname import get_channel_name
from gmprocess.stationtrace import StationTrace, PROCESS_LEVELS
from gmprocess.stationstream import StationStream

NZCATWINDOW = 5 * 60  # number of seconds to search around in GeoNet EQ catalog

TEXT_HDR_ROWS = 16
FP_HDR_ROWS = 10

MMPS_TO_CMPS = 1 / 10.0

COLS_PER_ROW = 10

# These formats are described in this document:
# ftp://ftp.geonet.org.nz/strong/processed/Docs/GNS%20ACCELEROGRAM%20DATA%20FILE%20FORMAT%202012-03-15.docx


def is_geonet(filename):
    """Check to see if file is a New Zealand GNS V1 or V2 strong motion file.

    Args:
        filename (str): Path to possible GNS V1/V2 data file.
    Returns:
        bool: True if GNS V1/V2, False otherwise.
    """
    logging.debug("Checking if format is geonet.")
    try:
        line = open(filename, 'rt').readline()
        if line.find('GNS Science') >= 0:
            c1 = line.find('Corrected accelerogram') >= 0
            c2 = line.find('Uncorrected accelerogram') >= 0
            if c1 or c2:
                return True
        return False
    except UnicodeDecodeError:
        return False


def read_geonet(filename, **kwargs):
    """Read New Zealand GNS V1/V2 strong motion file.

    There is one extra key in the Stats object for each Trace -
    "process_level".
    This will be set to either "V1" or "V2".

    Args:
        filename (str): Path to possible GNS V1/V2 data file.
        kwargs (ref): Other arguments will be ignored.

    Returns:
        Stream: Obspy Stream containing three channels of acceleration data
        (cm/s**2).
    """
    logging.debug("Starting read_geonet.")
    trace1, offset1, _ = _read_channel(filename, 0)
    trace2, offset2, _ = _read_channel(filename, offset1)
    trace3, _, _ = _read_channel(filename, offset2)

    # occasionally, geonet horizontal components are
    # identical.  To handle this, we'll set the second
    # channel to whatever isn't the first one.
    channel1 = trace1.stats['channel']
    channel2 = trace2.stats['channel']
    channel3 = trace3.stats['channel']
    if channel1 == channel2:
        if channel1.endswith('1'):
            trace2.stats['channel'] = trace2.stats['channel'][0:2] + '2'
        elif channel1.endswith('2'):
            trace2.stats['channel'] = trace2.stats['channel'][0:2] + '1'
        else:
            raise Exception(
                'Could not resolve duplicate channels in %s'
                % trace1.stats['station'])
    if channel2 == channel3:
        if channel2.endswith('2'):
            trace3.stats['channel'] = trace2.stats['channel'][0:2] + '1'
        elif channel2.endswith('1'):
            trace3.stats['channel'] = trace2.stats['channel'][0:2] + '2'
        else:
            raise Exception(
                'Could not resolve duplicate channels in %s'
                % trace1.stats['station'])

    traces = [trace1, trace2, trace3]
    stream = StationStream(traces)

    return [stream]


def _read_channel(filename, line_offset):
    """Read channel data from GNS V1 text file.

    Args:
        filename (str): Input GNS V1 filename.
        line_offset (int): Line offset to beginning of channel text block.
    Returns:
        tuple: (obspy Trace, int line offset)
    """
    # read station and location strings from text header
    with open(filename, 'rt') as f:
        for _ in range(line_offset):
            next(f)
        lines = [next(f) for x in range(TEXT_HDR_ROWS)]

    # this code supports V1 and V2 format files.  Which one is this?
    data_format = 'V2'
    if lines[0].lower().find('uncorrected') >= 0:
        data_format = 'V1'

    # parse out the station code, name, and component string
    # from text header
    station = lines[1].split()[1]
    logging.debug('station: %s' % station)
    name = lines[2].replace(' ', '_').strip()
    component = lines[12].split()[1]

    # parse the instrument type from the text header
    instrument = lines[3].split()[1]

    # parse the sensor resolution from the text header
    resolution_str = lines[4].split()[1]
    resolution = int(re.search('\d+', resolution_str).group())

    # read floating point header array
    skip_header = line_offset + TEXT_HDR_ROWS
    hdr_data = np.genfromtxt(filename, skip_header=skip_header,
                             max_rows=FP_HDR_ROWS)

    # parse header dictionary from float header array
    hdr = _read_header(hdr_data, station, name,
                       component, data_format,
                       instrument, resolution)

    # according to the powers that defined the Network.Station.Channel.Location
    # "standard", Location is a two character field.  Most data providers,
    # including GeoNet here, don't provide this.  We'll flag it as "--".
    hdr['location'] = '--'

    # read in the data, handling cases where last row has less than 10 columns
    if hdr['npts'] % COLS_PER_ROW != 0:
        nrows = int(np.floor(hdr['npts'] / COLS_PER_ROW))
        nrows2 = 1
    else:
        nrows = int(np.ceil(hdr['npts'] / COLS_PER_ROW))
        nrows2 = 0
    skip_header2 = line_offset + TEXT_HDR_ROWS + FP_HDR_ROWS
    widths = [8] * COLS_PER_ROW
    data = np.genfromtxt(filename, skip_header=skip_header2,
                         max_rows=nrows, filling_values=np.nan,
                         delimiter=widths)
    data = data.flatten()
    if nrows2:
        skip_header3 = skip_header2 + nrows
        data2 = np.genfromtxt(filename, skip_header=skip_header3,
                              max_rows=nrows2, filling_values=np.nan)
        data = np.hstack((data, data2))
        nrows += nrows2

    # for debugging, read in the velocity data
    nvel = hdr_data[3, 4]
    if nvel:
        if nvel % COLS_PER_ROW != 0:
            nvel_rows = int(np.floor(nvel / COLS_PER_ROW))
            nvel_rows2 = 1
        else:
            nvel_rows = int(np.ceil(nvel / COLS_PER_ROW))
            nvel_rows2 = 0
        skip_header_vel = line_offset + TEXT_HDR_ROWS + FP_HDR_ROWS + nrows
        widths = [8] * COLS_PER_ROW
        velocity = np.genfromtxt(filename, skip_header=skip_header_vel,
                                 max_rows=nvel_rows, filling_values=np.nan,
                                 delimiter=widths)
        velocity = velocity.flatten()
        if nrows2:
            skip_header_vel = skip_header_vel + nvel_rows
            vel2 = np.genfromtxt(filename, skip_header=skip_header_vel,
                                 max_rows=nvel_rows2, filling_values=np.nan)
            velocity = np.hstack((velocity, vel2))
        velocity *= MMPS_TO_CMPS
    else:
        velocity = np.array([])

    # for V2 files, there are extra blocks of data we need to skip containing
    # velocity and displacement data
    if data_format == 'V2':
        velrows = int(np.ceil(hdr_data[3, 4] / COLS_PER_ROW))
        disrows = int(np.ceil(hdr_data[3, 5] / COLS_PER_ROW))
        nrows = nrows + velrows + disrows

    data *= MMPS_TO_CMPS  # convert to cm/s**2
    trace = StationTrace(data, Stats(hdr))

    response = {'input_units': 'counts', 'output_units': 'cm/s^2'}
    trace.setProvenance('remove_response', response)

    offset = skip_header2 + nrows

    return (trace, offset, velocity)


def _read_header(hdr_data, station, name, component, data_format,
                 instrument, resolution):
    """Construct stats dictionary from header lines.

    Args:
        hdr_data (ndarray): (10,10) numpy array containing header data.
        station (str): Station code obtained from previous text portion of
            header.
        location (str): Location string obtained from previous text portion
            of header.
        component (str): Component direction (N18E, S72W, etc.)
    Returns:
        Dictionary containing fields:
            - network "NZ"
            - station
            - channel H1,H2,or Z.
            - location
            - sampling_rate Samples per second.
            - delta Interval between samples (seconds)
            - calib Calibration factor (always 1.0)
            - npts Number of samples in record.
            - starttime Datetime object containing start of record.
            - standard:
              - station_name
              - units "acc"
              - source 'New Zealand Institute of Geological and Nuclear
                Science'
              - horizontal_orientation
              - instrument_period
              - instrument_damping
              - processing_time
              - process_level
              - sensor_serial_number
              - instrument
              - comments
              - structure_type
              - corner_frequency
              - source_format
            - coordinates:
              - lat Latitude of station.
              - lon Longitude of station.
              - elevation Elevation of station.
            - format_specific:
              - sensor_bit_resolution

    """
    hdr = {}
    standard = {}
    coordinates = {}
    format_specific = {}
    hdr['station'] = station
    standard['station_name'] = name
    if data_format == 'V1':
        hdr['sampling_rate'] = hdr_data[4, 0]
        sampling_rate = hdr['sampling_rate']
        hdr['delta'] = 1 / hdr['sampling_rate']
    else:
        hdr['delta'] = hdr_data[6, 5]
        hdr['sampling_rate'] = 1 / hdr['delta']
        # V2 files have been resampled, we need sensor rate for
        # channel naming.
        sampling_rate = 1 / hdr_data[6, 4]
    hdr['calib'] = 1.0
    if data_format == 'V1':
        hdr['npts'] = int(hdr_data[3, 0])
    else:
        hdr['npts'] = int(hdr_data[3, 3])
    hdr['network'] = 'NZ'
    standard['units'] = 'acc'
    standard['source'] = ('New Zealand Institute of Geological and '
                          'Nuclear Science')
    logging.debug('component: %s' % component)
    if component == 'Up':
        standard['horizontal_orientation'] = np.nan
        hdr['channel'] = get_channel_name(
            sampling_rate,
            is_acceleration=True,
            is_vertical=True,
            is_north=False)
    else:
        _, angle = _get_channel(component)
        logging.debug('angle: %s' % angle)
        standard['horizontal_orientation'] = float(angle)
        if (angle > 315 or angle < 45) or (angle > 135 and angle < 225):
            hdr['channel'] = get_channel_name(
                sampling_rate,
                is_acceleration=True,
                is_vertical=False,
                is_north=True)
        else:
            hdr['channel'] = get_channel_name(
                sampling_rate,
                is_acceleration=True,
                is_vertical=False,
                is_north=False)

    logging.debug('channel: %s' % hdr['channel'])
    hdr['location'] = '--'

    # figure out the start time
    milliseconds = hdr_data[3, 9]
    seconds = int(milliseconds / 1000)
    microseconds = int(np.round(milliseconds / 1000.0 - seconds))
    year = int(hdr_data[0, 8])
    month = int(hdr_data[0, 9])
    day = int(hdr_data[1, 8])
    hour = int(hdr_data[1, 9])
    minute = int(hdr_data[3, 8])
    hdr['starttime'] = datetime(
        year, month, day, hour, minute, seconds, microseconds)

    # figure out station coordinates
    coordinates['latitude'] = -hdr_data[2, 0] + \
        ((hdr_data[2, 1] + hdr_data[2, 2] / 60.0) / 60.0)
    coordinates['longitude'] = hdr_data[2, 3] + \
        ((hdr_data[2, 4] + hdr_data[2, 5] / 60.0) / 60.0)
    coordinates['elevation'] = 0.0

    # get other standard metadata
    standard['instrument_period'] = 1 / hdr_data[4, 0]
    standard['instrument_damping'] = hdr_data[4, 1]
    standard['process_time'] = ''
    standard['process_level'] = PROCESS_LEVELS[data_format]
    logging.debug("process_level: %s" % data_format)
    standard['sensor_serial_number'] = ''
    standard['instrument'] = instrument
    standard['comments'] = ''
    standard['structure_type'] = ''
    standard['corner_frequency'] = np.nan
    standard['source_format'] = 'geonet'

    # get format specific metadata
    format_specific['sensor_bit_resolution'] = resolution

    hdr['coordinates'] = coordinates
    hdr['standard'] = standard
    hdr['format_specific'] = format_specific

    return hdr


def _get_channel(component):
    """Determine channel name string from component string.

    Args:
        component (str): String like "N28E".

    Returns:
        str: Channel (H1,H2,Z)
    """
    start_direction = component[0]
    end_direction = component[-1]
    angle = int(re.search("\\d+", component).group())
    if start_direction == 'N':
        if end_direction == 'E':
            comp_angle = angle
        else:
            comp_angle = 360 - angle
    else:
        if end_direction == 'E':
            comp_angle = 180 - angle
        else:
            comp_angle = 180 + angle
    c1 = comp_angle > 315 or comp_angle < 45
    c2 = comp_angle > 135 and comp_angle < 225
    if c1 or c2:
        channel = 'H1'
    else:
        channel = 'H2'

    return (channel, comp_angle)
