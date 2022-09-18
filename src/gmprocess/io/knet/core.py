#!/usr/bin/env python

# stdlib imports
from datetime import datetime, timedelta
import re
import os
import logging

# third party
from obspy.core.trace import Stats
import numpy as np

# local imports
from gmprocess.io.seedname import get_channel_name, get_units_type
from gmprocess.core.stationtrace import StationTrace, PROCESS_LEVELS
from gmprocess.core.stationstream import StationStream
from gmprocess.io.utils import is_binary


TEXT_HDR_ROWS = 17
TIMEFMT = "%Y/%m/%d %H:%M:%S"
COLS_PER_LINE = 8

HDR1 = "Origin Time"
HDR2 = "Station Code"

SRC = "Japan National Research Institute for Earth Science and Disaster Resilience"


def is_knet(filename, config=None):
    """Check to see if file is a Japanese NIED/KNET strong motion file.

    Args:
        filename (str):
            Path to possible NIED/KNET data file.
        config (dict):
            Dictionary containing configuration.

    Returns:
        bool: True if NIED/KNET, False otherwise.
    """
    logging.debug("Checking if format is knet.")
    if is_binary(filename):
        return False
    if not os.path.isfile(filename):
        return False
    try:
        open(filename, "rt").read(os.stat(filename).st_size)
    except UnicodeDecodeError:
        return False
    try:
        with open(filename, "rt") as f:
            lines = [next(f) for x in range(TEXT_HDR_ROWS)]
            if lines[0].startswith(HDR1) and lines[5].startswith(HDR2):
                return True
    except BaseException:
        return False
    return False


def read_knet(filename, config=None, **kwargs):
    """Read Japanese KNET strong motion file.

    Args:
        filename (str):
            Path to possible KNET data file.
        config (dict):
            Dictionary containing configuration.
        kwargs (ref):
            Other arguments will be ignored.

    Returns:
        Stream: Obspy Stream containing three channels of acceleration data
            (cm/s**2).
    """
    logging.debug("Starting read_knet.")
    if not is_knet(filename, config):
        raise Exception(f"{filename} is not a valid KNET file")

    # Parse the header portion of the file
    with open(filename, "rt") as f:
        lines = [next(f) for x in range(TEXT_HDR_ROWS)]

    hdr = {}
    coordinates = {}
    standard = {}
    hdr["network"] = "BO"
    hdr["station"] = lines[5].split()[2]
    logging.debug(f"station: {hdr['station']}")
    standard["station_name"] = ""

    # according to the powers that defined the Network.Station.Channel.Location
    # "standard", Location is a two character field.  Most data providers,
    # including KNET here, don't provide this.  We'll flag it as "--".
    hdr["location"] = "--"

    coordinates["latitude"] = float(lines[6].split()[2])
    coordinates["longitude"] = float(lines[7].split()[2])
    coordinates["elevation"] = float(lines[8].split()[2])

    hdr["sampling_rate"] = float(re.search("\\d+", lines[10].split()[2]).group())
    hdr["delta"] = 1 / hdr["sampling_rate"]
    standard["units_type"] = "acc"
    standard["units_type"] = "cm/s/s"

    dir_string = lines[12].split()[1].strip()
    # knet files have directions listed as N-S, E-W, or U-D,
    # whereas in kiknet those directions are '4', '5', or '6'.
    if dir_string in ["N-S", "1", "4"]:
        hdr["channel"] = get_channel_name(
            hdr["sampling_rate"], is_acceleration=True, is_vertical=False, is_north=True
        )
    elif dir_string in ["E-W", "2", "5"]:
        hdr["channel"] = get_channel_name(
            hdr["sampling_rate"],
            is_acceleration=True,
            is_vertical=False,
            is_north=False,
        )
    elif dir_string in ["U-D", "3", "6"]:
        hdr["channel"] = get_channel_name(
            hdr["sampling_rate"], is_acceleration=True, is_vertical=True, is_north=False
        )
    else:
        raise Exception(f"KNET: Could not parse direction {lines[12].split()[1]}")

    logging.debug(f"channel: {hdr['channel']}")
    scalestr = lines[13].split()[2]
    parts = scalestr.split("/")
    num = float(parts[0].replace("(gal)", ""))
    den = float(parts[1])
    calib = num / den
    hdr["calib"] = calib

    duration = float(lines[11].split()[2])

    hdr["npts"] = int(duration * hdr["sampling_rate"])

    timestr = " ".join(lines[9].split()[2:4])
    # The K-NET and KiK-Net data logger adds a 15s time delay
    # this is removed here
    sttime = datetime.strptime(timestr, TIMEFMT) - timedelta(seconds=15.0)
    # Shift the time to utc (Japanese time is 9 hours ahead)
    sttime = sttime - timedelta(seconds=9 * 3600.0)
    hdr["starttime"] = sttime

    # read in the data - there is a max of 8 columns per line
    # the code below handles the case when last line has
    # less than 8 columns
    if hdr["npts"] % COLS_PER_LINE != 0:
        nrows = int(np.floor(hdr["npts"] / COLS_PER_LINE))
        nrows2 = 1
    else:
        nrows = int(np.ceil(hdr["npts"] / COLS_PER_LINE))
        nrows2 = 0
    data = np.genfromtxt(
        filename, skip_header=TEXT_HDR_ROWS, max_rows=nrows, filling_values=np.nan
    )
    data = data.flatten()
    if nrows2:
        skip_header = TEXT_HDR_ROWS + nrows
        data2 = np.genfromtxt(
            filename, skip_header=skip_header, max_rows=nrows2, filling_values=np.nan
        )
        data = np.hstack((data, data2))
        nrows += nrows2

    # apply the correction factor we're given in the header
    data *= calib

    # fill out the rest of the standard dictionary
    standard["units_type"] = get_units_type(hdr["channel"])
    standard["horizontal_orientation"] = np.nan
    standard["vertical_orientation"] = np.nan
    standard["instrument_period"] = np.nan
    standard["instrument_damping"] = np.nan
    standard["process_time"] = ""
    standard["process_level"] = PROCESS_LEVELS["V1"]
    standard["sensor_serial_number"] = ""
    standard["instrument"] = ""
    standard["comments"] = ""
    standard["structure_type"] = ""
    if dir_string in ["1", "2", "3"]:
        standard["structure_type"] = "borehole"

    standard["corner_frequency"] = np.nan
    standard["units"] = "acc"
    standard["source"] = SRC
    standard["source_format"] = "knet"
    head, tail = os.path.split(filename)
    standard["source_file"] = tail or os.path.basename(head)

    # these fields can be used for instrument correction
    # when data is in counts
    standard["instrument_sensitivity"] = np.nan
    standard["volts_to_counts"] = np.nan

    hdr["coordinates"] = coordinates
    hdr["standard"] = standard

    # create a Trace from the data and metadata
    trace = StationTrace(data.copy(), Stats(hdr.copy()))
    response = {"input_units": "counts", "output_units": "cm/s^2"}
    trace.setProvenance("remove_response", response)

    stream = StationStream(traces=[trace], config=config)
    return [stream]
