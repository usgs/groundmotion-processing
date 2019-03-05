# stdlib imports
from datetime import datetime
import logging

# third party imports
import numpy as np
from obspy.core.trace import Stats

# local imports
from gmprocess.exception import GMProcessException
from gmprocess.io.seedname import get_channel_name
from gmprocess.stationstream import StationStream
from gmprocess.stationtrace import StationTrace, PROCESS_LEVELS
from gmprocess.io.utils import is_evenly_spaced, resample_uneven_trace

VOLUMES = {
    'V1': {
        'TEXT_HDR_ROWS': 13,
        'INT_HDR_ROWS': 6,
        'INT_FMT': 16 * [5],
        'FLT_HDR_ROWS': 7,
        'FLT_FMT': 8 * [10],
        'COL_FMT': [8, 7, 7, 7, 7, 7, 7, 7, 7, 7]
    }
}
USC_ORIENTATIONS = {
    400: ('Vertical', 'Vert'),
    500: ('Up', 'Up'),
    600: ('Down', 'Down'),
    700: ('Longitudinal (relative to structure)', 'Long'),
    800: ('', 'Tran')
}

# Number of decimals for time deltas to be considered unique
NUM_DECIMALS = 3


def is_usc(filename):
    """Check to see if file is a USC strong motion file.

    Args:
        filename (str): Path to possible USC V1 data file.
    Returns:
        bool: True if USC , False otherwise.
    """
    logging.debug("Checking if format is usc.")
    # USC requires unique integer values
    # in column 73-74 on all text header lines
    # excluding the first file line

    try:
        f = open(filename, 'rt')
        first_line = f.readline()

        if first_line.find('OF UNCORRECTED ACCELEROGRAM DATA OF') >= 0:
            start = 0
            stop = 12
        elif first_line.find('CORRECTED ACCELEROGRAM') >= 0:
            start = 1
            stop = 13
            line = f.readline()
        else:
            return False
        counter = stop
        while counter > start:
            line = f.readline()
            try:
                int(line[72:74])
            except ValueError:
                return False
            counter -= 1
        return True
    except UnicodeDecodeError:
        return False


def read_usc(filename, **kwargs):
    """Read USC V1 strong motion file.

    Args:
        filename (str): Path to possible USC V1 data file.
        kwargs (ref): Ignored by this function.
    Returns:
        Stream: Obspy Stream containing three channels of acceleration data
        (cm/s**2).
    """
    logging.debug("Starting read_usc.")
    if not is_usc(filename):
        raise Exception('%s is not a valid USC file' % filename)

    # Check for Location
    location = kwargs.get('location', '')

    f = open(filename, 'rt')
    first_line = f.readline()
    f.close()

    if first_line.find('OF UNCORRECTED ACCELEROGRAM DATA OF') >= 0:
        stream = read_volume_one(filename, location=location)
    else:
        raise GMProcessException('Not a supported volume.')
    return stream


def read_volume_one(filename, location=''):
    """Read channel data from USC volume 1 text file.

    Args:
        filename (str): Input DMG V1 filename.
    Returns:
        tuple: (list of obspy Trace, int line offset)
    """
    volume = VOLUMES['V1']
    # count the number of lines in the file
    with open(filename) as f:
        line_count = sum(1 for _ in f)
    # read as many channels as are present in the file
    line_offset = 0
    stream = StationStream([])
    while line_offset < line_count:
        trace, line_offset = _read_channel(
            filename, line_offset, volume, location=location)
        # store the trace if the station type is in the valid_station_types
        # list or store the trace if there is no valid_station_types list
        if trace is not None:
            stream.append(trace)

    return [stream]


def _read_channel(filename, line_offset, volume, location=''):
    """Read channel data from USC V1 text file.

    Args:
        filename (str): Input USC V1 filename.
        line_offset (int): Line offset to beginning of channel text block.
        volume (dictionary): Dictionary of formatting information
    Returns:
        tuple: (obspy Trace, int line offset)
    """
    # Parse the header portion of the file
    try:
        with open(filename, 'rt') as f:
            for _ in range(line_offset):
                next(f)
            lines = [next(f) for x in range(volume['TEXT_HDR_ROWS'])]
    # Accounts for blank lines at end of files
    except StopIteration:
        return (None, 1 + line_offset)
    # read in lines of integer data
    skiprows = line_offset + volume['TEXT_HDR_ROWS']
    int_data = np.genfromtxt(filename, skip_header=skiprows,
                             max_rows=volume['INT_HDR_ROWS'], dtype=np.int32,
                             delimiter=volume['INT_FMT']).flatten()

    # read in lines of float data
    skiprows += volume['INT_HDR_ROWS'] + 1
    flt_data = np.genfromtxt(filename, skip_header=skiprows,
                             max_rows=volume['FLT_HDR_ROWS'], dtype=np.float64,
                             delimiter=volume['FLT_FMT']).flatten()
    hdr = _get_header_info(int_data, flt_data, lines, 'V1', location=location)
    skiprows += volume['FLT_HDR_ROWS']
    # read in the data
    nrows = int(np.floor(hdr['npts'] * 2 / 10))
    all_data = np.genfromtxt(filename, skip_header=skiprows,
                             max_rows=nrows, dtype=np.float64,
                             delimiter=volume['COL_FMT'])
    data = all_data.flatten()[1::2]
    times = all_data.flatten()[0::2]

    trace = StationTrace(data.copy(), Stats(hdr.copy()))

    if not is_evenly_spaced(times, NUM_DECIMALS):
        trace = resample_uneven_trace(trace, times, data)

    response = {'input_units': 'counts', 'output_units': 'cm/s^2'}
    trace.setProvenance('remove_response', response)

    # set new offset
    new_offset = skiprows + nrows
    new_offset += 1  # there is an 'end of record' line after the data

    return (trace, new_offset)


def _get_header_info(int_data, flt_data, lines, volume, location=''):
    """Return stats structure from various headers.

    Output is a dictionary like this:
     - network (str): 'LA'
     - station (str)
     - channel (str): Determined using COSMOS_ORIENTATIONS
     - location (str): Default is '--'
     - starttime (datetime)
     - duration (float)
     - sampling_rate (float)
     - npts (int)
     - coordinates:
       - latitude (float)
       - longitude (float)
       - elevation (float)
    - standard (Defaults are either np.nan or '')
      - horizontal_orientation (float): Rotation from north (degrees)
      - instrument_period (float): Period of sensor (Hz)
      - instrument_damping (float): Fraction of critical
      - process_time (datetime): Reported date of processing
      - process_level: Either 'V0', 'V1', 'V2', or 'V3'
      - station_name (str): Long form station description
      - sensor_serial_number (str): Reported sensor serial
      - instrument (str): See SENSOR_TYPES
      - comments (str): Processing comments
      - structure_type (str): See BUILDING_TYPES
      - corner_frequency (float): Sensor corner frequency (Hz)
      - units (str): See UNITS
      - source (str): Network source description
      - source_format (str): Always cosmos
    - format_specific
      - fractional_unit (float): Units of digitized acceleration
            in file (fractions of g)

    Args:
        int_data (ndarray): Array of integer data
        flt_data (ndarray): Array of float data
        lines (list): List of text headers (str)

    Returns:
        dictionary: Dictionary of header/metadata information
    """
    hdr = {}
    coordinates = {}
    standard = {}
    format_specific = {}
    if volume == 'V1':
        hdr['duration'] = flt_data[2]
        hdr['npts'] = int_data[27]
        hdr['sampling_rate'] = (hdr['npts'] - 1) / hdr['duration']

        # Get required parameter number
        hdr['network'] = 'LA'
        hdr['station'] = str(int_data[8])
        logging.debug('station: %s' % hdr['station'])
        horizontal_angle = int_data[26]
        logging.debug('horizontal: %s' % horizontal_angle)
        if (horizontal_angle in USC_ORIENTATIONS or
                (horizontal_angle >= 0 and horizontal_angle <= 360)):
            if horizontal_angle in USC_ORIENTATIONS:
                channel = USC_ORIENTATIONS[horizontal_angle][1].upper()
                if channel == 'UP' or channel == 'DOWN' or channel == 'VERT':
                    channel = get_channel_name(
                        hdr['sampling_rate'],
                        is_acceleration=True,
                        is_vertical=True,
                        is_north=False)
            elif (
                horizontal_angle > 315 or
                horizontal_angle < 45 or
                (horizontal_angle > 135 and horizontal_angle < 225)
            ):
                channel = get_channel_name(
                    hdr['sampling_rate'],
                    is_acceleration=True,
                    is_vertical=False,
                    is_north=True)
            else:
                channel = get_channel_name(
                    hdr['sampling_rate'],
                    is_acceleration=True,
                    is_vertical=False,
                    is_north=False)
            horizontal_orientation = horizontal_angle
            hdr['channel'] = channel
            logging.debug('channel: %s' % hdr['channel'])
        else:
            errstr = ('Not enough information to distinguish horizontal from '
                      'vertical channels.')
            raise GMProcessException(errstr)

        if location == '':
            hdr['location'] = '--'
        else:
            hdr['location'] = location
        month = str(int_data[21])
        day = str(int_data[22])
        year = str(int_data[23])
        time = str(int_data[24])
        tstr = month + '/' + day + '/' + year + '_' + time
        starttime = datetime.strptime(tstr, '%m/%d/%Y_%H%M')
        hdr['starttime'] = starttime

        # Get coordinates
        lat_deg = int_data[9]
        lat_min = int_data[10]
        lat_sec = int_data[11]
        lon_deg = int_data[12]
        lon_min = int_data[13]
        lon_sec = int_data[14]
        # Check for southern hemisphere, default is northern
        if lines[4].find('STATION USC#') >= 0:
            idx = lines[4].find('STATION USC#') + 12
            if 'S' in lines[4][idx:]:
                lat_sign = -1
            else:
                lat_sign = 1
        else:
            lat_sign = 1
        # Check for western hemisphere, default is western
        if lines[4].find('STATION USC#') >= 0:
            idx = lines[4].find('STATION USC#') + 12
            if 'W' in lines[4][idx:]:
                lon_sign = -1
            else:
                lon_sign = 1
        else:
            lon_sign = -1
        latitude = lat_sign * _dms2dd(lat_deg, lat_min, lat_sec)
        longitude = lon_sign * _dms2dd(lon_deg, lon_min, lon_sec)
        coordinates['latitude'] = latitude
        coordinates['longitude'] = longitude
        coordinates['elevation'] = np.nan
        # Get standard paramaters
        standard['horizontal_orientation'] = float(horizontal_orientation)
        standard['instrument_period'] = flt_data[0]
        standard['instrument_damping'] = flt_data[1]
        standard['process_time'] = ''
        station_line = lines[5]
        station_length = int(lines[5][72:74])
        name = station_line[:station_length]
        standard['station_name'] = name
        standard['sensor_serial_number'] = ''
        standard['instrument'] = ''
        standard['comments'] = ''
        standard['units'] = 'acc'
        standard['structure_type'] = ''
        standard['process_level'] = PROCESS_LEVELS['V1']
        standard['corner_frequency'] = np.nan
        standard['source'] = ('Los Angeles Basin Seismic Network, University '
                              'of Southern California')
        standard['source_format'] = 'usc'
        # Get format specific
        format_specific['fractional_unit'] = flt_data[4]
    # Set dictionary
    hdr['standard'] = standard
    hdr['coordinates'] = coordinates
    hdr['format_specific'] = format_specific
    return hdr


def _dms2dd(degrees, minutes, seconds):
    """Helper method for converting degrees, minutes, seconds to decimal.

    Args:
        degrees (int): Lat/Lon degrees.
        minutes (int): Lat/Lon minutes.
        seconds (int): Lat/Lon seconds.
    Returns:
        float: Lat/Lon in decimal degrees
    """
    decimal = degrees + float(minutes) / 60.0 + float(seconds) / 3600.0
    return decimal
