#!/usr/bin/env python

# stdlib imports
import os
from datetime import datetime
import re
import copy
import logging

# third party imports
import numpy as np
from scipy import constants

# local
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace, PROCESS_LEVELS
from gmprocess.io.seedname import get_channel_name, get_units_type
from gmprocess.io.utils import is_binary


TIMEFMT = "%d/%m/%Y %H:%M:%S.%f"
FLOATRE = r"[-+]?[0-9]*\.?[0-9]+"
INTRE = "[-+]?[0-9]*"

# 20/07/2017 22:30:58.000000
TIME_RE = r"[0-9]{2}/[0-9]{2}/[0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}\.?[0-9]*"

TEXT_HDR_ROWS = 18

COLWIDTH = 12
NCOLS = 3

SOURCE = "National Strong-Motion Network of Turkey (TR-NSMN)"
SOURCE_FORMAT = "NSMN"
NETWORK = "TK"

LEVELS = {"VOL1DS": "V1"}

DECIG_TO_GALS = (constants.g * 100) / 10

MARKER = "STRONG GROUND MOTION RECORDS OF TURKIYE"

ENCODING = "ISO-8859-1"
# ENCODING = 'utf-16-be'


def is_nsmn(filename, config=None):
    """Check to see if file is Turkish NSMN format.

    Args:
        filename (str):
            Path to possible Turkish NSMN format.
        config (dict):
            Dictionary containing configuration.

    Returns:
        bool: True if Turkish NSMN format, otherwise False.
    """
    if is_binary(filename):
        return False
    with open(filename, "rt", encoding=ENCODING) as f:
        line = f.readline()
        if MARKER in line:
            return True

    return False


def read_nsmn(filename, config=None):
    """Read the Turkish NSMN strong motion data format.

    Args:
        filename (str):
            path to NSMN data file.
        config (dict):
            Dictionary containing configuration.

    Returns:
        list: Sequence of one StationStream object containing 3 StationTrace
        objects.
    """
    header = _read_header(filename)
    header1 = copy.deepcopy(header)
    header2 = copy.deepcopy(header)
    header3 = copy.deepcopy(header)
    header1["standard"]["horizontal_orientation"] = 0.0
    header1["standard"]["vertical_orientation"] = np.nan
    header1["channel"] = get_channel_name(header["sampling_rate"], True, False, True)
    header1["standard"]["units_type"] = get_units_type(header1["channel"])
    header2["standard"]["horizontal_orientation"] = 90.0
    header2["standard"]["vertical_orientation"] = np.nan
    header2["channel"] = get_channel_name(header["sampling_rate"], True, False, False)
    header2["standard"]["units_type"] = get_units_type(header2["channel"])
    header3["standard"]["horizontal_orientation"] = 0.0
    header3["standard"]["vertical_orientation"] = np.nan
    header3["channel"] = get_channel_name(header["sampling_rate"], True, True, False)
    header3["standard"]["units_type"] = get_units_type(header3["channel"])

    # three columns of NS, EW, UD
    # data = np.genfromtxt(filename, skip_header=TEXT_HDR_ROWS,
    #                      delimiter=[COLWIDTH] * NCOLS, encoding=ENCODING)
    data = np.loadtxt(filename, skiprows=TEXT_HDR_ROWS, encoding=ENCODING)
    data1 = data[:, 0]
    data2 = data[:, 1]
    data3 = data[:, 2]
    trace1 = StationTrace(data=data1, header=header1)
    response = {"input_units": "counts", "output_units": "cm/s^2"}
    trace1.setProvenance("remove_response", response)
    trace2 = StationTrace(data=data2, header=header2)
    trace2.setProvenance("remove_response", response)
    trace3 = StationTrace(data=data3, header=header3)
    trace3.setProvenance("remove_response", response)
    stream = StationStream(traces=[trace1, trace2, trace3], config=config)
    return [stream]


def _read_header(filename):
    header = {}
    standard = {}
    coords = {}
    format_specific = {}
    with open(filename, "rt", encoding=ENCODING) as f:
        lines = [next(f) for x in range(TEXT_HDR_ROWS)]
        # fill out the standard dictionary
        standard["source"] = SOURCE
        standard["source_format"] = SOURCE_FORMAT
        standard["instrument"] = lines[9].split(":")[1].strip()
        standard["sensor_serial_number"] = lines[10].split(":")[1].strip()
        standard["process_level"] = PROCESS_LEVELS["V1"]
        standard["process_time"] = ""
        standard["station_name"] = lines[1].split(":")[1].strip()
        standard["structure_type"] = ""
        standard["corner_frequency"] = np.nan
        standard["units_type"] = "acc"
        standard["units"] = "cm/s/s"
        standard["instrument_period"] = np.nan
        standard["instrument_damping"] = np.nan
        standard["horizontal_orientation"] = np.nan
        standard["comments"] = " ".join(lines[15:17]).replace("\n", "")
        head, tail = os.path.split(filename)
        standard["source_file"] = tail or os.path.basename(head)

        # these fields can be used for instrument correction
        # when data is in counts
        standard["instrument_sensitivity"] = np.nan
        standard["volts_to_counts"] = np.nan

        # fill out the stats stuff
        stimestr = re.search(TIME_RE, lines[11]).group()
        # 20/07/2017 22:30:58.000000 (GMT)
        stime = datetime.strptime(stimestr, TIMEFMT)
        header["starttime"] = stime
        header["npts"] = int(lines[12].split(":")[1].strip())
        header["delta"] = float(lines[13].split(":")[1].strip())
        header["sampling_rate"] = 1 / header["delta"]
        header["duration"] = header["npts"] * header["delta"]
        header["channel"] = ""
        header["station"] = lines[6].split(":")[1].strip()
        header["location"] = "--"
        header["network"] = NETWORK

        coordstr = lines[7].split(":")[1].replace("-", "")
        lat_str, lon_str = re.findall(FLOATRE, coordstr)
        altparts = lines[8].split(":")
        altitude = 0.0
        if len(altparts) > 1 and len(altparts[1].strip()):
            altitude = float(altparts[1].strip())
        else:
            logging.warn("Setting elevation to 0.0")
        coords = {
            "latitude": float(lat_str),
            "longitude": float(lon_str),
            "elevation": altitude,
        }

        header["coordinates"] = coords
        header["standard"] = standard
        header["format_specific"] = format_specific

        return header
