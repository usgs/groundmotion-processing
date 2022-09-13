# stdlib imports
import os
from collections import OrderedDict
from datetime import datetime, timedelta
import logging

# third party imports
import numpy as np
from obspy.core.trace import Stats

# local imports
from gmprocess.io.seedname import get_channel_name, get_units_type
from gmprocess.core.stationtrace import StationTrace, PROCESS_LEVELS
from gmprocess.core.stationstream import StationStream
from gmprocess.io.utils import is_binary

DATE_FMT = "%Y/%m/%d-%H:%M:%S.%f"

GMT_OFFSET = 8 * 3600  # CWB data is in local time, GMT +8

HDR_ROWS = 22
COLWIDTH = 10
NCOLS = 4


def is_cwb(filename, config=None):
    """Check to see if file is a Taiwan Central Weather Bureau strong motion
    file.

    Args:
        filename (str):
            Path to possible CWB data file.
        config (dict):
            Dictionary containing configuration.

    Returns:
        bool: True if CWB, False otherwise.
    """
    logging.debug("Checking if format is cwb.")
    if is_binary(filename):
        return False
    try:
        f = open(filename, "rt", encoding="utf-8")
        line = f.readline()
        f.close()
        if line.startswith("#Earthquake Information"):
            return True
    except UnicodeDecodeError:
        return False
    return False


def read_cwb(filename, config=None, **kwargs):
    """Read Taiwan Central Weather Bureau strong motion file.

    Args:
        filename (str):
            Path to possible CWB data file.
        config (dict):
            Dictionary containing configuration.
        kwargs (ref):
            Other arguments will be ignored.

    Returns:
        Stream: Obspy Stream containing three channels of acceleration
        data (cm/s**2).
    """
    logging.debug("Starting read_cwb.")
    if not is_cwb(filename, config):
        raise Exception(f"{filename} is not a valid CWB strong motion data file.")
    f = open(filename, "rt", encoding="utf-8")
    # according to the powers that defined the Network.Station.Channel.Location
    # "standard", Location is a two character field.  Most data providers,
    # including CWB here, don't provide this.  We'll flag it as "--".
    data = np.genfromtxt(
        filename, skip_header=HDR_ROWS, delimiter=[COLWIDTH] * NCOLS
    )  # time, Z, NS, EW

    hdr = _get_header_info(f, data)
    f.close()

    head, tail = os.path.split(filename)
    hdr["standard"]["source_file"] = tail or os.path.basename(head)

    hdr_z = hdr.copy()
    hdr_z["channel"] = get_channel_name(
        hdr["sampling_rate"], is_acceleration=True, is_vertical=True, is_north=False
    )
    hdr_z["standard"]["horizontal_orientation"] = np.nan
    hdr_z["standard"]["vertical_orientation"] = np.nan
    hdr_z["standard"]["units_type"] = get_units_type(hdr_z["channel"])

    hdr_h1 = hdr.copy()
    hdr_h1["channel"] = get_channel_name(
        hdr["sampling_rate"], is_acceleration=True, is_vertical=False, is_north=True
    )
    hdr_h1["standard"]["horizontal_orientation"] = np.nan
    hdr_h1["standard"]["vertical_orientation"] = np.nan
    hdr_h1["standard"]["units_type"] = get_units_type(hdr_h1["channel"])

    hdr_h2 = hdr.copy()
    hdr_h2["channel"] = get_channel_name(
        hdr["sampling_rate"], is_acceleration=True, is_vertical=False, is_north=False
    )
    hdr_h2["standard"]["horizontal_orientation"] = np.nan
    hdr_h2["standard"]["vertical_orientation"] = np.nan
    hdr_h2["standard"]["units_type"] = get_units_type(hdr_h2["channel"])

    stats_z = Stats(hdr_z)
    stats_h1 = Stats(hdr_h1)
    stats_h2 = Stats(hdr_h2)

    response = {"input_units": "counts", "output_units": "cm/s^2"}
    trace_z = StationTrace(data=data[:, 1], header=stats_z)
    trace_z.setProvenance("remove_response", response)

    trace_h1 = StationTrace(data=data[:, 2], header=stats_h1)
    trace_h1.setProvenance("remove_response", response)

    trace_h2 = StationTrace(data=data[:, 3], header=stats_h2)
    trace_h2.setProvenance("remove_response", response)

    stream = StationStream([trace_z, trace_h1, trace_h2], config=config)
    return [stream]


def _get_header_info(file, data):
    """Return stats structure from various headers.

    Output is a dictionary like this:
     - network (str): Always TW
     - station (str)
     - channel (str)
     - location (str): Default is '--'
     - starttime (datetime)
     - duration (float)
     - sampling_rate (float)
     - delta (float)
     - npts (int)
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
      - source_format (str): Always cwb
    - format_specific
        - dc_offset_z (float)
        - dc_offset_h1 (float)
        - dc_offset_h2 (float)

    Args:
        file (TextIOWrapper): File object containing data
        data (ndarray): Array of strong motion data

    Returns:
        dictionary: Dictionary of header/metadata information
    """
    hdr = OrderedDict()
    coordinates = {}
    standard = {}
    format_specific = {}
    hdr["location"] = "--"
    while True:
        line = file.readline()
        if line.startswith("#StationCode"):
            hdr["station"] = line.split(":")[1].strip()
            logging.debug(f"station: {hdr['station']}")
        if line.startswith("#StationName"):
            standard["station_name"] = line.split(":")[1].strip()
            logging.debug(f"station_name: {standard['station_name']}")
        if line.startswith("#StationLongitude"):
            coordinates["longitude"] = float(line.split(":")[1].strip())
        if line.startswith("#StationLatitude"):
            coordinates["latitude"] = float(line.split(":")[1].strip())
        if line.startswith("#StartTime"):
            timestr = ":".join(line.split(":")[1:]).strip()
            hdr["starttime"] = datetime.strptime(timestr, DATE_FMT)
        if line.startswith("#RecordLength"):
            hdr["duration"] = float(line.split(":")[1].strip())
        if line.startswith("#SampleRate"):
            hdr["sampling_rate"] = int(line.split(":")[1].strip())
        if line.startswith("#InstrumentKind"):
            standard["instrument"] = line.split(":")[1].strip()
        if line.startswith("#AmplitudeMAX. U:"):
            format_specific["dc_offset_z"] = float(line.split("~")[1])
        if line.startswith("#AmplitudeMAX. N:"):
            format_specific["dc_offset_h1"] = float(line.split("~")[1])
        if line.startswith("#AmplitudeMAX. E:"):
            format_specific["dc_offset_h2"] = float(line.split("~")[1])
        if line.startswith("#Data"):
            break

    # correct start time to GMT
    hdr["starttime"] = hdr["starttime"] - timedelta(seconds=GMT_OFFSET)
    nrows, _ = data.shape
    # Add some optional information to the header
    hdr["network"] = "TW"
    hdr["delta"] = 1 / hdr["sampling_rate"]
    hdr["calib"] = 1.0
    standard["units_type"] = "acc"
    standard["units"] = "cm/s^2"
    hdr["source"] = "Taiwan Central Weather Bureau"
    hdr["npts"] = nrows
    secs = int(data[-1, 0])
    microsecs = int((data[-1, 0] - secs) * 1e6)
    hdr["endtime"] = hdr["starttime"] + timedelta(seconds=secs, microseconds=microsecs)

    # Set defaults
    logging.warning("Setting elevation to 0.0")
    coordinates["elevation"] = 0.0
    if "longitude" not in coordinates:
        coordinates["longitude"] = np.nan
    if "latitude" not in coordinates:
        coordinates["latitude"] = np.nan
    standard["instrument_period"] = np.nan
    standard["instrument_damping"] = np.nan
    standard["process_time"] = ""
    standard["process_level"] = PROCESS_LEVELS["V1"]
    standard["sensor_serial_number"] = ""
    standard["comments"] = ""
    standard["structure_type"] = ""
    standard["corner_frequency"] = np.nan
    standard["source"] = (
        "Taiwan Strong Motion Instrumentation Program " + "via Central Weather Bureau"
    )
    standard["source_format"] = "cwb"

    # these fields can be used for instrument correction
    # when data is in counts
    standard["instrument_sensitivity"] = np.nan
    standard["volts_to_counts"] = np.nan

    if "station_name" not in standard:
        standard["station_name"] = ""
    if "instrument" not in standard:
        standard["instrument"] = ""
    if "dc_offset_z" not in format_specific:
        format_specific["dc_offset_z"] = np.nan
    if "dc_offset_h2" not in format_specific:
        format_specific["dc_offset_h2"] = np.nan
    if "dc_offset_h1" not in format_specific:
        format_specific["dc_offset_h1"] = np.nan
    # Set dictionary
    hdr["standard"] = standard
    hdr["coordinates"] = coordinates
    hdr["format_specific"] = format_specific
    return hdr
