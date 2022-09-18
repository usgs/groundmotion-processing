#!/usr/bin/env python

# stdlib imports
import os
from datetime import datetime, timedelta
import re
import logging

# third party
from obspy.core.trace import Stats
import numpy as np
import pytz

# local imports
from gmprocess.utils.constants import UNIT_CONVERSIONS, DATA_DIR
from gmprocess.io.usc.core import is_usc
from gmprocess.io.seedname import get_channel_name, get_units_type
from gmprocess.core.stationtrace import StationTrace, TIMEFMT, PROCESS_LEVELS
from gmprocess.core.stationstream import StationStream
from gmprocess.io.utils import is_evenly_spaced, resample_uneven_trace
from gmprocess.io.utils import is_binary


V1_TEXT_HDR_ROWS = 13
V1_INT_HDR_ROWS = 7
V1_REAL_HDR_ROWS = 7

V2_TEXT_HDR_ROWS = 25
V2_INT_HDR_ROWS = 7
V2_INT_FMT = [5] * 16
V2_REAL_HDR_ROWS = 13
V2_REAL_FMT = [10] * 8

V1_MARKER = "UNCORRECTED ACCELEROGRAM DATA"
V2_MARKER = "CORRECTED ACCELEROGRAM"
V3_MARKER = "RESPONSE AND FOURIER AMPLITUDE SPECTRA"

DATE_PATTERNS = [
    "[0-9]{2}/[0-9]{2}/[0-9]{2}",
    "[0-9]{2}/[0-9]{1}/[0-9]{2}",
    "[0-9]{1}/[0-9]{2}/[0-9]{2}",
    "[0-9]{1}/[0-9]{1}/[0-9]{2}",
    "[0-9]{2}-[0-9]{2}-[0-9]{2}",
    "[0-9]{2}-[0-9]{1}-[0-9]{2}",
    "[0-9]{1}-[0-9]{2}-[0-9]{2}",
    "[0-9]{1}-[0-9]{1}-[0-9]{2}",
]

TIME_MATCH = r"[0-9]{2}:[0-9]{2}:..\.[0-9]{1}"

code_file = DATA_DIR / "fdsn_codes.csv"


CODES, SOURCES1, SOURCES2 = np.genfromtxt(
    code_file,
    skip_header=1,
    usecols=(0, 1, 2),
    encoding="latin-1",
    unpack=True,
    dtype=bytes,
    delimiter=",",
)
CODES = CODES.astype(str)

UNITS = ["acc", "vel", "disp"]


def _get_date(line):
    """Parse a datetime object with month/day/year info found from string."""
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, line)
        if match is not None:
            date = datetime.strptime(match.group(), "%m/%d/%y")
            return date
    return None


def _get_time(line):
    """Parse a timdelta object with hour, minute, fractional second info found
    from string.
    """
    match = re.search(TIME_MATCH, line)
    if match is not None:
        parts = match.group().split(":")
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(float(parts[2]))
        microseconds = int((float(parts[2]) - second) * 1e6)
        seconds = ((hour * 3600) + minute * 60) + second
        dt = timedelta(seconds=seconds, microseconds=microseconds)
        return dt
    return None


def is_dmg(filename, config=None):
    """Check to see if file is a DMG strong motion file.

    Notes:
        CSMIP is synonymous to as DMG in this reader.

    Args:
        filename (str):
            Path to possible DMG data file.
        config (dict):
            Dictionary containing configuration.

    Returns:
        bool: True if DMG , False otherwise.
    """
    logging.debug("Checking if format is dmg.")
    if is_binary(filename):
        return False
    try:
        f = open(filename, "rt", encoding="utf-8")
        first_line = f.readline().upper()
        second_line = f.readline().upper()
        third_line = f.readline().upper()
        f.close()

        # dmg/csmip both have the same markers so is_usc must be checked
        if first_line.find(V1_MARKER) >= 0 and not is_usc(filename, config):
            return True
        elif first_line.find(V2_MARKER) >= 0 and not is_usc(filename, config):
            if second_line.find(V1_MARKER) >= 0:
                return True
        elif first_line.find(V3_MARKER) >= 0 and not is_usc(filename, config):
            if second_line.find(V2_MARKER) >= 0 and third_line.find(V1_MARKER) >= 0:
                return True
        else:
            return False
    except UnicodeDecodeError:
        return False


def read_dmg(filename, config=None, **kwargs):
    """Read DMG strong motion file.

    Notes:
        CSMIP is synonymous to as DMG in this reader.

    Args:
        filename (str):
            Path to possible DMG data file.
        config (dict):
            Dictionary containing configuration.
        kwargs (ref):
            units (str): String determining which timeseries is return. Valid
                    options include 'acc', 'vel', 'disp'. Default is 'acc'.
            Other arguments will be ignored.

    Returns:
        Stream: Obspy Stream containing three channels of acceleration data
        (cm/s**2).
    """
    logging.debug("Starting read_dmg.")
    if not is_dmg(filename, config):
        raise Exception(f"{filename} is not a valid DMG strong motion data file.")

    # Check for units and location
    units = kwargs.get("units", "acc")
    location = kwargs.get("location", "")

    if units not in UNITS:
        raise Exception("DMG: Not a valid choice of units.")

    # Check for DMG format and determine volume type
    line = open(filename, "rt", encoding="utf-8").readline()
    if is_dmg(filename, config):
        if line.lower().find("uncorrected") >= 0:
            reader = "V1"
        elif line.lower().find("corrected") >= 0:
            reader = "V2"
        elif line.lower().find("response") >= 0:
            reader = "V3"

    # Count the number of lines in the file
    with open(filename, encoding="utf-8") as f:
        line_count = sum(1 for _ in f)

    # Read as many channels as are present in the file
    line_offset = 0
    trace_list = []
    while line_offset < line_count:
        if reader == "V2":
            traces, line_offset = _read_volume_two(
                filename, line_offset, location=location, units=units
            )
            if traces is not None:
                trace_list += traces
        elif reader == "V1":
            traces, line_offset = _read_volume_one(
                filename, line_offset, location=location, units=units, config=config
            )
            if traces is not None:
                trace_list += traces
        else:
            raise ValueError("DMG: Not a supported volume.")

    stream = StationStream([], config=config)
    for trace in trace_list:
        # For our purposes, we only want acceleration, so lets only return
        # that; we may need to change this later if others start using this
        # code and want to read in the other data.
        if trace.stats["standard"]["units_type"] == units:
            stream.append(trace)
    return [stream]


def _read_volume_one(filename, line_offset, location="", units="acc", config=None):
    """Read channel data from DMG Volume 1 text file.

    Args:
        filename (str):
            Input DMG V1 filename.
        line_offset (int):
            Line offset to beginning of channel text block.
        units (str):
            units to get.
        config (dict):
            Configuration options.

    Returns:
        tuple: (list of obspy Trace, int line offset)
    """
    # Parse the header portion of the file
    try:
        with open(filename, "rt", encoding="utf-8") as f:
            for _ in range(line_offset):
                next(f)
            lines = [next(f) for x in range(V1_TEXT_HDR_ROWS)]
    # Accounts for blank lines at end of files
    except StopIteration:
        return (None, 1 + line_offset)

    unit = _get_units(lines[11])
    # read in lines of integer data
    skip_rows = V1_TEXT_HDR_ROWS + line_offset
    int_data = _read_lines(skip_rows, V1_INT_HDR_ROWS, V2_INT_FMT, filename)
    int_data = int_data[0:100].astype(np.int32)

    # read in lines of float data
    skip_rows += V1_INT_HDR_ROWS
    flt_data = _read_lines(skip_rows, V1_REAL_HDR_ROWS, V2_REAL_FMT, filename)
    skip_rows += V1_REAL_HDR_ROWS

    # ------------------------------------------------------------------------------- #
    # according to the powers that defined the Network.Station.Channel.Location
    # "standard", Location is a two character field.  Most data providers,
    # including csmip/dmg here, don't always provide this.  We'll flag it as
    # "--".

    # Update Feb 4, 2022
    # In order to be able to store structural/geotech array data in the ASDF file, we
    # HAVE to use location code to uniquely identify the different instruments. The
    # arrays can only be read in as StreamArrays and not StreamCollections. In such
    # cases we will use the channel number as location code so that the data can be
    # saved.
    # ------------------------------------------------------------------------------- #

    hdr = _get_header_info_v1(
        int_data, flt_data, lines, "V1", location=location, config=config
    )
    head, tail = os.path.split(filename)
    hdr["standard"]["source_file"] = tail or os.path.basename(head)

    # sometimes (??) a line of text is inserted in between the float header and
    # the beginning of the data. Let's check for this...
    with open(filename, "rt", encoding="utf-8") as f:
        for _ in range(skip_rows):
            next(f)
        test_line = f.readline()

    has_text = re.search("[A-Z]+|[a-z]+", test_line) is not None
    if has_text:
        skip_rows += 1
        widths = [9] * 8
        max_rows = int(np.ceil(hdr["npts"] / 8))
        data = _read_lines(skip_rows, max_rows, widths, filename)
        acc_data = data[: hdr["npts"]]
        evenly_spaced = True
        # Sometimes, npts is incrrectly specified, leading to nans
        # in the resulting data. Fix that here
        if np.any(np.isnan(acc_data)):
            while np.isnan(acc_data[-1]):
                acc_data = acc_data[:-1]
            hdr["npts"] = len(acc_data)
    else:
        # acceleration data is interleaved between time data
        max_rows = int(np.ceil(hdr["npts"] / 5))
        widths = [7] * 10
        data = _read_lines(skip_rows, max_rows, widths, filename)
        acc_data = data[1::2][: hdr["npts"]]
        times = data[0::2][: hdr["npts"]]
        evenly_spaced = is_evenly_spaced(times)

    if unit in UNIT_CONVERSIONS:
        acc_data *= UNIT_CONVERSIONS[unit]
        logging.debug(f"Data converted from {unit} to cm/s/s")
    else:
        raise ValueError(f"DMG: {unit} is not a supported unit.")

    acc_trace = StationTrace(acc_data.copy(), Stats(hdr.copy()), config=config)

    # Check if the times were included in the file but were not evenly spaced
    if not evenly_spaced:
        acc_trace = resample_uneven_trace(acc_trace, times, acc_data, config=config)

    response = {"input_units": "counts", "output_units": "cm/s^2"}
    acc_trace.setProvenance("remove_response", response)

    traces = [acc_trace]
    new_offset = skip_rows + max_rows + 1  # there is an end of record line
    return (traces, new_offset)


def _read_volume_two(filename, line_offset, location="", units="acc"):
    """Read channel data from DMG text file.

    Args:
        filename (str):
            Input DMG V2 filename.
        line_offset (int):
            Line offset to beginning of channel text block.
        units (str):
            Units to get.

    Returns:
        tuple: (list of obspy Trace, int line offset)
    """
    try:
        with open(filename, "rt", encoding="utf-8") as f:
            for _ in range(line_offset):
                next(f)
            lines = [next(f) for x in range(V2_TEXT_HDR_ROWS)]
    # Accounts for blank lines at end of files
    except StopIteration:
        return (None, 1 + line_offset)

    # read in lines of integer data
    skip_rows = V2_TEXT_HDR_ROWS + line_offset
    int_data = _read_lines(skip_rows, V2_INT_HDR_ROWS, V2_INT_FMT, filename)
    int_data = int_data[0:100].astype(np.int32)

    # read in lines of float data
    skip_rows += V2_INT_HDR_ROWS
    flt_data = _read_lines(skip_rows, V2_REAL_HDR_ROWS, V2_REAL_FMT, filename)
    flt_data = flt_data[:100]
    skip_rows += V2_REAL_HDR_ROWS

    # according to the powers that defined the Network.Station.Channel.Location
    # "standard", Location is a two character field.  Most data providers,
    # including csmip/dmg here, don't always provide this.  We'll flag it as
    # "--".
    hdr = _get_header_info(int_data, flt_data, lines, "V2", location=location)
    head, tail = os.path.split(filename)
    hdr["standard"]["source_file"] = tail or os.path.basename(head)

    traces = []
    # read acceleration data
    if hdr["npts"] > 0:
        acc_rows, acc_fmt, unit = _get_data_format(filename, skip_rows, hdr["npts"])
        acc_data = _read_lines(skip_rows + 1, acc_rows, acc_fmt, filename)
        acc_data = acc_data[: hdr["npts"]]
        if unit in UNIT_CONVERSIONS:
            acc_data *= UNIT_CONVERSIONS[unit]
            logging.debug(f"Data converted from {unit} to cm/s/s")
        else:
            raise ValueError(f"DMG: {unit} is not a supported unit.")
        acc_trace = StationTrace(acc_data.copy(), Stats(hdr.copy()))

        response = {"input_units": "counts", "output_units": "cm/s^2"}
        acc_trace.setProvenance("remove_response", response)

        if units == "acc":
            traces += [acc_trace]
        skip_rows += int(acc_rows) + 1

    # -------------------------------------------------------------------------
    # NOTE: The way we were initially reading velocity and displacement data
    # was not correct. I'm deleting it for now since we don't need it. If/when
    # we revisit this we need to be more careful about how this is handled.
    # -------------------------------------------------------------------------

    # read velocity data
    vel_hdr = hdr.copy()
    vel_hdr["standard"]["units_type"] = "vel"
    vel_hdr["npts"] = int_data[63]
    if vel_hdr["npts"] > 0:
        vel_rows, vel_fmt, unit = _get_data_format(filename, skip_rows, vel_hdr["npts"])
        vel_data = _read_lines(skip_rows + 1, vel_rows, vel_fmt, filename)
        vel_data = vel_data[: vel_hdr["npts"]]
        skip_rows += int(vel_rows) + 1

    # read displacement data
    disp_hdr = hdr.copy()
    disp_hdr["standard"]["units_type"] = "disp"
    disp_hdr["standard"]["units"] = "cm"
    disp_hdr["npts"] = int_data[65]
    if disp_hdr["npts"] > 0:
        disp_rows, disp_fmt, unit = _get_data_format(
            filename, skip_rows, disp_hdr["npts"]
        )
        disp_data = _read_lines(skip_rows + 1, disp_rows, disp_fmt, filename)
        disp_data = disp_data[: disp_hdr["npts"]]
        skip_rows += int(disp_rows) + 1

    # there is an 'end of record' line after the data]
    new_offset = skip_rows + 1
    return (traces, new_offset)


def _get_header_info_v1(int_data, flt_data, lines, level, location="", config=None):
    """Return stats structure from various V1 headers.

    Output is a dictionary like this:
     - network (str): Default is '--'. Determined using COSMOS_NETWORKS
     - station (str)
     - channel (str)
     - location (str): Default is '--'
     - starttime (datetime)
     - sampling_rate (float)
     - delta (float)
     - coordinates:
       - latitude (float)
       - longitude (float)
       - elevation (float): Default is np.nan
    - standard (Defaults are either np.nan or '')
      - horizontal_orientation (float): Rotation from north (degrees)
      - instrument_period (float): Period of sensor (Hz)
      - instrument_damping (float): Fraction of critical
      - process_time (datetime): Reported date of processing
      - process_level: Either 'V0', 'V1', 'V2', or 'V3'
      - station_name (str): Long form station description
      - sensor_serial_number (str): Reported sensor serial
      - instrument (str)
      - comments (str): Processing comments
      - structure_type (str)
      - corner_frequency (float): Sensor corner frequency (Hz)
      - units (str)
      - source (str): Network source description
      - source_format (str): Always dmg
    - format_specific
      - sensor_sensitivity (float): Transducer sensitivity (cm/g)
      - time_sd (float): Standard deviaiton of time steop (millisecond)
      - fractional_unit (float): Units of digitized acceleration
            in file (fractions of g)
      - scaling_factor (float): Scaling used for converting acceleration
            from g/10 to cm/sec/sec
      - low_filter_corner (float): Filter corner for low frequency
            V2 filtering (Hz)
      - high_filter_corner (float): Filter corner for high frequency
            V2 filtering (Hz)

    Args:
        int_data (ndarray):
            Array of integer data
        flt_data (ndarray):
            Array of float data
        lines (list):
            List of text headers (str)
        level (str):
            Process level code (V0, V1, V2, V3)
        config (dict):
            Config options.

    Returns:
        dictionary: Dictionary of header/metadata information
    """
    hdr = {}
    coordinates = {}
    standard = {}
    format_specific = {}

    # Required metadata
    code = ""
    if lines[0].find("CDMG") > -1:
        code = "CDMG"

    if code.upper() in CODES:
        network = code.upper()
        idx = np.argwhere(CODES == network)[0][0]
        source = SOURCES1[idx].decode("utf-8") + ", " + SOURCES2[idx].decode("utf-8")
    else:
        # newer files have a record_id.network.station.location.channel thing
        # in the 4th line
        recinfo = lines[3][0:23]
        try:
            parts = recinfo.strip().split(".")
            network = parts[1].upper()
            idx = np.argwhere(CODES == network)[0][0]
            source = (
                SOURCES1[idx].decode("utf-8") + ", " + SOURCES2[idx].decode("utf-8")
            )
        except BaseException:
            network = "--"
            source = "unknown"
    hdr["network"] = network
    logging.debug(f"network: {network}")
    station_line = lines[4]
    station = station_line[12:17].strip()
    logging.debug(f"station: {station}")
    hdr["station"] = station
    angle = int_data[26]
    logging.debug(f"angle: {angle}")

    # newer files seem to have the *real* number of points in int header 32
    if int_data[32] != 0:
        hdr["npts"] = int_data[32]
    else:
        hdr["npts"] = int_data[27]
    reclen = flt_data[2]
    logging.debug(f"reclen: {reclen}")
    logging.debug(f"npts: {hdr['npts']}")
    hdr["sampling_rate"] = np.round((hdr["npts"] - 1) / reclen)
    logging.debug(f"sampling_rate: {hdr['sampling_rate']}")
    hdr["delta"] = 1 / hdr["sampling_rate"]
    hdr["channel"] = _get_channel(angle, hdr["sampling_rate"])
    # this format uses codes of 500/600 in this angle to indicate a vertical
    # channel Obspy freaks out with azimuth values > 360, so let's just say
    # horizontal angle is zero in these cases
    if hdr["channel"].endswith("Z"):
        angle = "0.0"
    logging.debug(f"channel: {hdr['channel']}")

    if config is not None:
        if "use_streamcollection" in config["read"]:
            if config["read"]["use_streamcollection"] is False:
                location = f"{int(lines[6][5:7]):02d}"

    if location == "":
        hdr["location"] = "--"
    else:
        hdr["location"] = location

    # parse the trigger time
    try:
        trigger_time = _get_date(lines[3]) + _get_time(lines[3])
        # sometimes these trigger times are in UTC, other times a different
        # time zone. Figure out if this is the case and modify start time
        # accordingly
        # look for three letter string that might be a time zone
        if "PDT" in lines[3] or "PST" in lines[3]:
            timezone = pytz.timezone("US/Pacific")
            utcoffset = timezone.utcoffset(trigger_time)
            # subtracting because we're going from pacific to utc
            trigger_time -= utcoffset

        hdr["starttime"] = trigger_time
    except BaseException:
        logging.warning(
            "No start time provided on trigger line. "
            "This must be set manually for network/station: "
            "%s/%s." % (hdr["network"], hdr["station"])
        )
        standard["comments"] = "Missing start time."

    # Coordinates
    latitude_str = station_line[20:27].strip()
    longitude_str = station_line[29:37].strip()
    latitude, longitude = _get_coords(latitude_str, longitude_str)
    coordinates["latitude"] = latitude
    coordinates["longitude"] = longitude
    logging.warning("Setting elevation to 0.0")
    coordinates["elevation"] = 0.0

    # Standard metadata
    standard["units_type"] = get_units_type(hdr["channel"])
    standard["units"] = "cm/s/s"
    standard["horizontal_orientation"] = float(angle)
    standard["vertical_orientation"] = np.nan
    standard["instrument_period"] = flt_data[0]
    standard["instrument_damping"] = flt_data[1]

    process_time = _get_date(lines[0])
    if process_time is not None:
        standard["process_time"] = process_time.strftime(TIMEFMT)
    else:
        standard["process_time"] = ""

    standard["process_level"] = PROCESS_LEVELS[level]
    logging.debug(f"process_level: {standard['process_level']}")
    if "comments" not in standard:
        standard["comments"] = ""
    standard["structure_type"] = lines[7][46:80].strip()
    standard["instrument"] = station_line[39:47].strip()
    standard["sensor_serial_number"] = station_line[53:57].strip()
    standard["corner_frequency"] = np.nan
    standard["source"] = source
    standard["source_format"] = "dmg"
    standard["station_name"] = lines[5][0:40].strip()

    # these fields can be used for instrument correction
    # when data is in counts
    standard["instrument_sensitivity"] = np.nan
    standard["volts_to_counts"] = np.nan

    # Format specific metadata
    format_specific["fractional_unit"] = flt_data[4]
    format_specific["sensor_sensitivity"] = flt_data[5]
    if flt_data[13] == -999:
        format_specific["time_sd"] = np.nan
    else:
        format_specific["time_sd"] = flt_data[13]
    # Set dictionary
    hdr["coordinates"] = coordinates
    hdr["standard"] = standard
    hdr["format_specific"] = format_specific
    return hdr


def _get_header_info(int_data, flt_data, lines, level, location=""):
    """Return stats structure from various headers.

    Output is a dictionary like this:
     - network (str): Default is '--' (unknown). Determined using
       COSMOS_NETWORKS
     - station (str)
     - channel (str)
     - location (str): Default is '--'
     - starttime (datetime)
     - sampling_rate (float)
     - delta (float)
     - coordinates:
       - latitude (float)
       - longitude (float)
       - elevation (float): Default is np.nan
    - standard (Defaults are either np.nan or '')
      - horizontal_orientation (float): Rotation from north (degrees)
      - instrument_period (float): Period of sensor (Hz)
      - instrument_damping (float): Fraction of critical
      - process_time (datetime): Reported date of processing
      - process_level: Either 'V0', 'V1', 'V2', or 'V3'
      - station_name (str): Long form station description
      - sensor_serial_number (str): Reported sensor serial
      - instrument (str)
      - comments (str): Processing comments
      - structure_type (str)
      - corner_frequency (float): Sensor corner frequency (Hz)
      - units (str)
      - source (str): Network source description
      - source_format (str): Always dmg
    - format_specific
      - sensor_sensitivity (float): Transducer sensitivity (cm/g)
      - time_sd (float): Standard deviaiton of time steop (millisecond)
      - fractional_unit (float): Units of digitized acceleration
            in file (fractions of g)
      - scaling_factor (float): Scaling used for converting acceleration
            from g/10 to cm/sec/sec
      - low_filter_corner (float): Filter corner for low frequency
            V2 filtering (Hz)
      - high_filter_corner (float): Filter corner for high frequency
            V2 filtering (Hz)

    Args:
        int_data (ndarray): Array of integer data
        flt_data (ndarray): Array of float data
        lines (list): List of text headers (str)
        level (str): Process level code (V0, V1, V2, V3)

    Returns:
        dictionary: Dictionary of header/metadata information
    """
    hdr = {}
    coordinates = {}
    standard = {}
    format_specific = {}

    # Required metadata
    name_length = int_data[29]
    station_name = re.sub(" +", " ", lines[6][:name_length]).strip()
    code = re.sub(" +", " ", lines[1][name_length:]).strip().split(" ")[-1][:2]
    if code.upper() in CODES:
        network = code.upper()
        idx = np.argwhere(CODES == network)[0][0]
        source = SOURCES1[idx].decode("utf-8") + ", " + SOURCES2[idx].decode("utf-8")
    else:
        network = "--"
        source = "unknown"
    hdr["network"] = network
    station_line = lines[5]
    station = station_line[12:17].strip()
    hdr["station"] = station
    angle = int_data[26]

    hdr["delta"] = flt_data[60]
    hdr["sampling_rate"] = 1 / hdr["delta"]
    hdr["channel"] = _get_channel(angle, hdr["sampling_rate"])

    # this format uses codes of 500/600 in this angle to indicate a vertical
    # channel Obspy freaks out with azimuth values > 360, so let's just say
    # horizontal angle is zero in these cases
    if hdr["channel"].endswith("Z"):
        angle = "0.0"

    if location == "":
        hdr["location"] = "--"
    else:
        hdr["location"] = location

    # parse the trigger time
    try:
        trigger_time = _get_date(lines[4]) + _get_time(lines[4])
        # sometimes these trigger times are in UTC, other times a different
        # time zone. Figure out if this is the case and modify start time
        # accordingly
        # look for three letter string that might be a time zone
        if "PDT" in lines[3] or "PST" in lines[3]:
            timezone = pytz.timezone("US/Pacific")
            utcoffset = timezone.utcoffset(trigger_time)
            # subtracting because we're going from pacific to utc
            trigger_time -= utcoffset
        hdr["starttime"] = trigger_time
    except BaseException:
        logging.warning(
            "No start time provided on trigger line. "
            "This must be set manually for network/station: "
            "%s/%s." % (hdr["network"], hdr["station"])
        )
        standard["comments"] = "Missing start time."

    hdr["npts"] = int_data[52]

    # Coordinates
    latitude_str = station_line[20:27].strip()
    longitude_str = station_line[29:37].strip()
    latitude, longitude = _get_coords(latitude_str, longitude_str)
    coordinates["latitude"] = latitude
    coordinates["longitude"] = longitude
    logging.warning("Setting elevation to 0.0")
    coordinates["elevation"] = 0.0

    # Standard metadata
    standard["units_type"] = get_units_type(hdr["channel"])
    standard["horizontal_orientation"] = float(angle)
    standard["vertical_orientation"] = np.nan
    standard["instrument_period"] = flt_data[0]
    standard["instrument_damping"] = flt_data[1]

    standard["process_time"] = _get_date(lines[1]).strftime(TIMEFMT)
    standard["process_level"] = PROCESS_LEVELS[level]
    if "comments" not in standard:
        standard["comments"] = ""
    standard["structure_type"] = lines[7][46:80].strip()
    standard["instrument"] = station_line[39:47].strip()
    standard["sensor_serial_number"] = station_line[53:57].strip()
    standard["corner_frequency"] = np.nan
    standard["units"] = "acc"
    standard["source"] = source
    standard["source_format"] = "dmg"
    standard["station_name"] = station_name

    # these fields can be used for instrument correction
    # when data is in counts
    standard["instrument_sensitivity"] = np.nan
    standard["volts_to_counts"] = np.nan

    # Format specific metadata
    format_specific["fractional_unit"] = flt_data[4]
    format_specific["sensor_sensitivity"] = flt_data[5]
    if flt_data[13] == -999:
        format_specific["time_sd"] = np.nan
    else:
        format_specific["time_sd"] = flt_data[13]
    format_specific["scaling_factor"] = flt_data[51]
    format_specific["low_filter_corner"] = flt_data[61]
    format_specific["high_filter_corner"] = flt_data[72]
    # Set dictionary
    hdr["coordinates"] = coordinates
    hdr["standard"] = standard
    hdr["format_specific"] = format_specific
    return hdr


def _get_coords(latitude_str, longitude_str):
    try:
        latitude = float(latitude_str[:-1])
        if latitude_str.upper().find("S") >= 0:
            latitude = -1 * latitude
    except BaseException:
        logging.warning(
            "No latitude or invalid latitude format provided. Setting to np.nan.",
            Warning,
        )
        latitude = np.nan
    try:
        longitude = float(longitude_str[:-1])
        if longitude_str.upper().find("W") >= 0:
            longitude = -1 * longitude
    except BaseException:
        logging.warning(
            "No longitude or invalid longitude format provided.",
            "Setting to np.nan.",
            Warning,
        )
        longitude = np.nan
    return (latitude, longitude)


def _get_channel(angle, sampling_rate):
    if angle == 500 or angle == 600 or (angle >= 0 and angle <= 360):
        if angle == 500 or angle == 600:
            channel = get_channel_name(
                sampling_rate, is_acceleration=True, is_vertical=True, is_north=False
            )
        elif angle >= 315 or angle < 45 or (angle >= 135 and angle < 225):
            channel = get_channel_name(
                sampling_rate, is_acceleration=True, is_vertical=False, is_north=True
            )
        else:
            channel = get_channel_name(
                sampling_rate, is_acceleration=True, is_vertical=False, is_north=False
            )
    else:
        errstr = (
            "Not enough information to distinguish horizontal from "
            "vertical channels."
        )
        raise BaseException("DMG: " + errstr)
    return channel


def _read_lines(skip_rows, max_rows, widths, filename):
    """Read lines of headers and.

    Args:
        skip_rows (int):
            Number of rows to skip.
        filename (str):
            Path to possible DMG data file.
    Returns:
        array-like: List of comments or array of data.
    """
    data_arr = np.genfromtxt(
        filename,
        skip_header=skip_rows,
        max_rows=max_rows,
        dtype=np.float64,
        delimiter=widths,
    ).flatten()
    return data_arr


def _get_data_format(filename, skip_rows, npts):
    """Read data header and return the format.

    Args:
        skip_rows (int):
            Number of rows to skip.
        filename (str):
            Path to possible DMG data file.
        npts (int):
            Number of data points.
    Returns:
        tuple: (int number of rows, list list of widths).
    """
    fmt_line = np.genfromtxt(filename, skip_header=skip_rows, max_rows=1, dtype=str)
    fmt = fmt_line[-1]
    # Check for a format in header or use default
    if fmt.find("f") >= 0 and fmt.find("(") >= 0 and fmt.find(")") >= 0:
        fmt = fmt.replace("(", "").replace(")", "")
        cols = int(fmt.split("f")[0])
        widths = int(fmt.split("f")[-1].split(".")[0])
    else:
        cols = 8
        widths = 10

    # Check for units
    line_string = " ".join(fmt_line).lower()
    physical_units = _get_units(line_string)

    fmt = [widths] * cols
    rows = np.ceil(npts / cols)
    return (rows, fmt, physical_units)


def _get_units(line):
    """
    Parse units from a text line.

    Args:
        line (str):
            text line which should contain units.
    """
    line = line.lower()
    if line.find("in units of") >= 0:
        units_start = line.find("in units of")
    elif line.find("units of") >= 0:
        units_start = line.find("units of")
    elif line.find("in") >= 0:
        units_start = line.find("in")

    units_section = line[units_start:].replace(".", " ")

    if "g/10" in units_section:
        physical_units = "g/10"
    elif (
        "10g" in units_section
        or "10*g" in units_section
        or "g10" in units_section
        or "g*10" in units_section
    ):
        physical_units = "g*10"
    elif "gal" in units_section:
        physical_units = "cm/s/s"
    elif "g" in units_section and "g/" not in units_section:
        physical_units = "g"
    elif (
        "cm/s/s" in units_section
        or "cm/sec/sec" in units_section
        or "cm/s^2" in units_section
        or "cm/s2" in units_section
        or "cm/sec^2" in units_section
        or "cm/sec2" in units_section
    ):
        physical_units = "cm/s/s"
    elif "cm/s" in units_section or "cm/sec" in units_section:
        physical_units = "cm/s"
    elif "cm" in units_section:
        physical_units = "cm"
    elif "in/s/s" in units_section or "in/sec/sec" in units_section:
        physical_units = "in/s/s"
    elif "in/s" in units_section or "in/sec" in units_section:
        physical_units = "in/s"
    elif "in" in units_section:
        physical_units = "in"
    else:
        physical_units = units_section
    return physical_units
