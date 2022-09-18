#!/usr/bin/env python

# stdlib imports
import os.path
from datetime import datetime
import re
import logging

# third party imports
import numpy as np
from scipy import constants
import pandas as pd

# local
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace, PROCESS_LEVELS
from gmprocess.io.seedname import get_channel_name
from gmprocess.io.utils import is_binary
from gmprocess.utils.constants import DATA_DIR


TIMEFMT = "%m/%d/%Y %H:%M:%S.%f"
FLOATRE = r"[-+]?[0-9]*\.?[0-9]+"
# INTRE = "[-+]?[0-9]*"
INTRE = r"(\+|-)?\d+"

# 2/27/2010 2:45:46.000
TIME_RE = r"[0-9]{1,2}/[0-9]{1,2}/[0-9]{4} [0-9]{1,2}:[0-9]{2}:" r"[0-9]{2}\.?[0-9]*"
TIME_RE2 = "[0-9]{1,2}/[0-9]{1,2}/[0-9]{4} [0-9]{1,2}:[0-9]{2}:[0-9]{2}"

TEXT_HDR_ROWS = 13
INT_HEADER_ROWS = 7
FLOAT_HEADER_ROWS = 7

NCOLS = 10

SOURCE = "UNIVERSIDAD DE CHILE - RENADIC"
SOURCE_FORMAT = "RENADIC"
NETWORK = "C"

LEVELS = {"VOL1DS": "V1"}

DECIG_TO_GALS = (constants.g * 100) / 10

MARKER = "UNIVERSIDAD DE CHILE - RENADIC"

ENCODING = "ISO-8859-1"

NORTH_CHANNELS = ["NS", "NZ", "L"]  # calling these north channels
WEST_CHANNELS = ["EW", "T"]
VERTICAL_CHANNELS = ["Z", "V"]

G10_TO_GALS = 980 / 10.0


def is_renadic(filename, config=None):
    """Check to see if file is Chilean RENADIC format.

    Args:
        filename (str):
            Path to file to check.
        config (dict):
            Dictionary containing configuration.

    Returns:
        bool: True if Chilean RENADIC supported, otherwise False.
    """
    if is_binary(filename):
        return False

    with open(filename, "rt", encoding=ENCODING) as f:
        lines = [next(f) for x in range(TEXT_HDR_ROWS)]

    if MARKER in lines[7]:
        return True

    return False


def read_renadic(filename, config=None, **kwargs):
    """Read the Chilean RENADIC strong motion data format.

    Args:
        filename (str):
            path to RENADIC data file.
        config (dict):
            Dictionary containing configuration.
        kwargs (ref):
            Other arguments will be ignored.

    Returns:
        list: Sequence of one StationStream object containing 3
        StationTrace objects.
    """
    # This network does not include station coordinates in the data files,
    # but they did provide a PDF table with information about each station,
    # including structure type (free field or something else) and the
    # coordinates
    tablefile = os.path.join(DATA_DIR, "station_coordinates.xlsx")
    table = pd.read_excel(tablefile, engine="openpyxl")

    with open(filename, "rt", encoding=ENCODING) as f:
        lines1 = [next(f) for x in range(TEXT_HDR_ROWS)]
    header1 = _read_header(lines1, filename, table)
    ndata_rows = int(np.ceil((header1["npts"] * 2) / NCOLS))

    skip_rows = TEXT_HDR_ROWS + INT_HEADER_ROWS + FLOAT_HEADER_ROWS
    data1 = _read_data(filename, skip_rows, header1["npts"])

    skip_rows += ndata_rows + 1
    with open(filename, "rt", encoding=ENCODING) as f:
        [next(f) for x in range(skip_rows)]
        lines2 = [next(f) for x in range(TEXT_HDR_ROWS)]

    header2 = _read_header(lines2, filename, table)
    skip_rows += TEXT_HDR_ROWS + INT_HEADER_ROWS + FLOAT_HEADER_ROWS
    data2 = _read_data(filename, skip_rows, header1["npts"])

    skip_rows += ndata_rows + 1
    with open(filename, "rt", encoding=ENCODING) as f:
        [next(f) for x in range(skip_rows)]
        lines3 = [next(f) for x in range(TEXT_HDR_ROWS)]

    header3 = _read_header(lines3, filename, table)
    skip_rows += TEXT_HDR_ROWS + INT_HEADER_ROWS + FLOAT_HEADER_ROWS
    data3 = _read_data(filename, skip_rows, header1["npts"])

    trace1 = StationTrace(data=data1, header=header1)
    response = {"input_units": "counts", "output_units": "cm/s^2"}
    trace1.setProvenance("remove_response", response)
    trace2 = StationTrace(data=data2, header=header2)
    trace2.setProvenance("remove_response", response)
    trace3 = StationTrace(data=data3, header=header3)
    trace3.setProvenance("remove_response", response)
    stream = StationStream(traces=[trace1, trace2, trace3], config=config)
    return [stream]


def _read_data(filename, skip_rows, npts):
    floatrows = (npts * 2) / NCOLS
    introws = int(floatrows)
    data = np.genfromtxt(
        filename,
        skip_header=skip_rows,
        max_rows=introws,
        delimiter=10 * [7],
        encoding=ENCODING,
    )
    data = data.flatten()
    if floatrows > introws:
        data2 = np.genfromtxt(
            filename,
            skip_header=skip_rows + introws,
            max_rows=1,
            delimiter=10 * [7],
            encoding=ENCODING,
        )
        data2 = data2.flatten()
        data = np.concatenate((data, data2))
    data = data[1::2]
    data *= G10_TO_GALS
    data = data[0:npts]
    return data


def _read_header(lines, filename, table):
    header = {}
    standard = {}
    coords = {}
    format_specific = {}

    # fill out the standard dictionary
    standard["source"] = SOURCE
    standard["source_format"] = SOURCE_FORMAT
    standard["instrument"] = ""
    standard["sensor_serial_number"] = ""
    standard["process_level"] = PROCESS_LEVELS["V1"]
    standard["process_time"] = lines[0].split(":")[1].strip()
    # station name line can look like this:
    # VI�A DEL MAR CENTRO S/N 675
    sparts = lines[5].split()
    station_name = " ".join(sparts[0 : sparts.index("S/N")])
    standard["station_name"] = station_name

    # this table gives us station coordinates and structure type
    station_row = table[table["Name"] == station_name]
    if not len(station_row):
        logging.warning("Unknown structure type.")
        standard["structure_type"] = ""
    else:
        row = station_row.iloc[0]
        standard["structure_type"] = row["Structure Type"]
    standard["corner_frequency"] = np.nan
    standard["units"] = "cm/s^2"
    standard["units_type"] = "acc"

    inst_dict = {}
    for part in lines[9].split(","):
        key, value = part.split("=")
        fvalue_str = re.search(FLOATRE, value.strip()).group()
        inst_dict[key.strip()] = float(fvalue_str)

    standard["instrument_period"] = inst_dict["INSTR PERIOD"]
    standard["instrument_damping"] = inst_dict["DAMPING"]
    standard["horizontal_orientation"] = np.nan
    standard["vertical_orientation"] = np.nan
    standard["comments"] = " ".join(lines[11:13]).replace("\n", "")
    head, tail = os.path.split(filename)
    standard["source_file"] = tail or os.path.basename(head)

    # this field can be used for instrument correction
    # when data is in counts
    standard["instrument_sensitivity"] = inst_dict["SENSITIVITY"]
    standard["volts_to_counts"] = np.nan

    # fill out the stats stuff
    try:
        stimestr = re.search(TIME_RE, lines[3]).group()
    except AttributeError:
        try:
            stimestr = re.search(TIME_RE2, lines[3]).group()
        except AttributeError:
            logging.warning("Setting time to epoch.")
            stimestr = "01/01/1970 00:00:00.000"

    # 2/27/2010 2:45:46.000 GMT
    stime = datetime.strptime(stimestr, TIMEFMT)

    # it appears that sometimes the trigger time is set to Jan 1, 1980
    # by default.
    if stime.year == 1980 and stime.month == 1 and stime.day == 1:
        fmt = "Trigger time set to %s in file %s"
        logging.warning(fmt % (str(stime), standard["source_file"]))

    header["starttime"] = stime
    npts, duration = re.findall(FLOATRE, lines[10])
    npts = int(npts)
    duration = float(duration)
    header["npts"] = npts
    header["delta"] = duration / (npts - 1)
    header["sampling_rate"] = (npts - 1) / duration
    header["duration"] = duration
    raw_channel = lines[6][9:11].strip()
    if raw_channel in NORTH_CHANNELS:
        channel = get_channel_name(header["sampling_rate"], True, False, True)
    elif raw_channel in WEST_CHANNELS:
        channel = get_channel_name(header["sampling_rate"], True, False, False)
    elif raw_channel in VERTICAL_CHANNELS:
        channel = get_channel_name(header["sampling_rate"], True, True, False)
    else:
        raise KeyError(f"Channel name {raw_channel} not defined")

    header["channel"] = channel
    header["station"] = lines[5].split()[-1]
    header["location"] = "--"
    header["network"] = NETWORK

    # these files seem to have all zeros for station coordinates!
    if not len(station_row):
        logging.warning(f"Could not find station match for {station_name}")
        coordparts = lines[4].split()
        lat = float(re.search(FLOATRE, coordparts[2]).group())
        lon = float(re.search(FLOATRE, coordparts[3]).group())
        if lon == 0 or lat == 0:
            logging.warning("Latitude or Longitude values are 0")
        if "S" in coordparts[2]:
            lat = -1 * lat
        if "W" in coordparts[3]:
            lon = -1 * lon
    else:
        row = station_row.iloc[0]
        lat = row["Lat"]
        lon = row["Lon"]

    altitude = 0.0
    logging.warning("Setting elevation to 0.0")
    coords = {"latitude": lat, "longitude": lon, "elevation": altitude}

    header["coordinates"] = coords
    header["standard"] = standard
    header["format_specific"] = format_specific

    return header
