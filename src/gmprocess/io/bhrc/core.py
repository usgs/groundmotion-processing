#!/usr/bin/env python

# stdlib imports
import os
import re

# third party imports
import numpy as np
from obspy.core.utcdatetime import UTCDateTime

# local
from gmprocess.utils.constants import UNIT_CONVERSIONS
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace, PROCESS_LEVELS
from gmprocess.io.seedname import get_channel_name, get_units_type
from gmprocess.io.utils import is_binary


INTIMEFMT = "%Y/%m/%d %H:%M:%S"
FLOATRE = r"[-+]?[0-9]*\.?[0-9]+"
INTRE = "[-+]?[0-9]*"

TEXT_HDR_ROWS = 13
INT_HDR_ROWS = 7
FLOAT_HDR_ROWS = 7
COLS_PER_ROW = 10
COLWIDTH = 13

SOURCE = "Road, Housing & Urban Development Research Center (BHRC)"
SOURCE_FORMAT = "BHRC"
NETWORK = "I1"

LEVELS = {"VOL1DS": "V1"}


def is_bhrc(filename, config=None):
    """Check to see if file is Iran's BHRC format.

    Args:
        filename (str):
            Path to possible BHRC format.
        config (dict):
            Dictionary containing configuration.

    Returns:
        bool: True if BHRC supported, otherwise False.
    """
    if is_binary(filename):
        return False
    try:
        with open(filename, "rt", encoding="utf-8") as f:
            lines = [next(f) for x in range(TEXT_HDR_ROWS)]

        has_line1 = lines[0].startswith("* VOL")
        has_line7 = lines[6].startswith("COMP")
        if has_line1 and has_line7:
            return True
    except UnicodeDecodeError:
        return False
    return False


def read_bhrc(filename, config=None, **kwargs):
    """Read the Iran BHRC strong motion data format.

    Args:
        filename (str):
            Path to BHRC data file.
        config (dict):
            Dictionary containing configuration.
        kwargs (ref):
            Other arguments will be ignored.

    Returns:
        list: Sequence of one StationStream object containing 3
        StationTrace objects.
    """
    header1, offset = _read_header_lines(filename, 0)
    data1, offset = _read_data(filename, offset, header1)
    header2, offset = _read_header_lines(filename, offset)
    data2, offset = _read_data(filename, offset, header2)
    header3, offset = _read_header_lines(filename, offset)
    data3, offset = _read_data(filename, offset, header3)
    trace1 = StationTrace(data1, header1)
    trace2 = StationTrace(data2, header2)
    trace3 = StationTrace(data3, header3)
    stream = StationStream([trace1, trace2, trace3], config=config)

    for tr in stream:
        if tr.stats.standard.process_level != PROCESS_LEVELS["V0"]:
            response = {"input_units": "counts", "output_units": "cm/s^2"}
            tr.setProvenance("remove_response", response)

    return [stream]


def _read_header_lines(filename, offset):
    """Read the header lines for each channel.

    Args:
        filename (str):
            Input BHRC file name.
        offset (int):
            Number of lines to skip from the beginning of the file.

    Returns:
        tuple: (header dictionary containing Stats dictionary with
        extra sub-dicts, updated offset rows)
    """
    with open(filename, "rt", encoding="utf-8") as f:
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
    station_info = lines[7][lines[7].index("Station") :]
    float_strings = re.findall(FLOATRE, station_info)
    (lat_str, lon_str, alt_str, lstr, tstr) = float_strings[0:5]
    component = lines[4].strip()
    if component == "V":
        angle = np.nan
    elif component == "L":
        angle = float(lstr)
    else:
        angle = float(tstr)
    coords = {
        "latitude": float(lat_str),
        "longitude": float(lon_str),
        "elevation": float(alt_str),
    }

    # fill out the standard dictionary
    standard["source"] = SOURCE
    standard["source_format"] = SOURCE_FORMAT
    standard["instrument"] = lines[1].split("=")[1].strip()
    standard["sensor_serial_number"] = ""
    volstr = lines[0].split()[1].strip()
    if volstr not in LEVELS:
        raise KeyError(f"Volume {volstr} files are not supported.")
    standard["process_level"] = PROCESS_LEVELS[LEVELS[volstr]]
    standard["process_time"] = ""
    station_name = lines[7][0 : lines[7].index("Station")].strip()
    standard["station_name"] = station_name
    standard["structure_type"] = ""
    standard["corner_frequency"] = np.nan
    standard["units"] = "cm/s/s"
    period_str, damping_str = re.findall(FLOATRE, lines[9])
    standard["instrument_period"] = float(period_str)
    if standard["instrument_period"] == 0:
        standard["instrument_period"] = np.nan
    standard["instrument_damping"] = float(damping_str)
    standard["horizontal_orientation"] = angle
    standard["vertical_orientation"] = np.nan
    standard["comments"] = ""
    head, tail = os.path.split(filename)
    standard["source_file"] = tail or os.path.basename(head)

    # these fields can be used for instrument correction
    # when data is in counts
    standard["instrument_sensitivity"] = np.nan
    standard["volts_to_counts"] = np.nan

    # fill out the stats stuff
    # we don't know the start of the trace
    header["starttime"] = UTCDateTime(1970, 1, 1)
    npts_str, dur_str = re.findall(FLOATRE, lines[10])
    header["npts"] = int(npts_str)
    header["duration"] = float(dur_str)
    header["delta"] = header["duration"] / (header["npts"] - 1)
    header["sampling_rate"] = 1 / header["delta"]
    if np.isnan(angle):
        header["channel"] = get_channel_name(
            header["sampling_rate"],
            is_acceleration=True,
            is_vertical=True,
            is_north=False,
        )
    elif (angle > 315 or angle < 45) or (angle > 135 and angle < 225):
        header["channel"] = get_channel_name(
            header["sampling_rate"],
            is_acceleration=True,
            is_vertical=False,
            is_north=True,
        )
    else:
        header["channel"] = get_channel_name(
            header["sampling_rate"],
            is_acceleration=True,
            is_vertical=False,
            is_north=False,
        )

    standard["units_type"] = get_units_type(header["channel"])

    part1 = lines[0].split(":")[1]
    stationcode = part1.split("/")[0].strip()
    header["station"] = stationcode
    header["location"] = "--"
    header["network"] = NETWORK

    header["coordinates"] = coords
    header["standard"] = standard
    header["format_specific"] = format_specific

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
    npoints = header["npts"]
    nrows = int(np.ceil(npoints / COLS_PER_ROW))
    data = np.genfromtxt(
        filename,
        skip_header=offset,
        max_rows=nrows,
        filling_values=np.nan,
        delimiter=widths,
    )
    data = data.flatten()
    data = data[0 : header["npts"]]

    # convert data to cm/s^2
    data *= UNIT_CONVERSIONS["g/10"]

    offset += nrows + 1  # there is an end of record marker line
    return (data, offset)
