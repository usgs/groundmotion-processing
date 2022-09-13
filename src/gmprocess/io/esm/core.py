#!/usr/bin/env python

# stdlib imports
from datetime import datetime
import os
import logging

# third party
from obspy.core.trace import Stats
import numpy as np

# local imports
from gmprocess.core.stationtrace import StationTrace, PROCESS_LEVELS
from gmprocess.core.stationstream import StationStream
from gmprocess.io.utils import is_binary


TEXT_HDR_ROWS = 64
# 20190728_160919.870
TIMEFMT = "%Y%m%d_%H%M%S.%f"
TIMEFMT2 = "%Y-%m-%dT%H:%M:%S.%f"


SRC = "ORFEUS Engineering Strong Motion Database"
FORMAT = "ESM"

HDR1 = "EVENT_NAME:"
HDR2 = "EVENT_ID:"


def is_esm(filename, config=None):
    """Check to see if file is an ESM strong motion file.

    Args:
        filename (str):
            Path to possible ESM strong motion file.
        config (dict):
            Dictionary containing configuration.

    Returns:
        bool: True if ESM, False otherwise.
    """
    logging.debug("Checking if format is esm.")
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
            if lines[0].startswith(HDR1) and lines[1].startswith(HDR2):
                return True
    except BaseException:
        return False
    return False


def read_esm(filename, config=None, **kwargs):
    """Read European ESM strong motion file.

    Args:
        filename (str):
            Path to possible ESM data file.
        config (dict):
            Dictionary containing configuration.
        kwargs (ref):
            Other arguments will be ignored.

    Returns:
        Stream: Obspy Stream containing one channels of acceleration data
            (cm/s**2).
    """
    logging.debug("Starting read_esm.")
    if not is_esm(filename, config):
        raise Exception(f"{filename} is not a valid ESM file")

    # Parse the header portion of the file
    header = {}
    with open(filename, "rt") as f:
        lines = [next(f) for x in range(TEXT_HDR_ROWS)]

    for line in lines:
        parts = line.split(":")
        key = parts[0].strip()
        value = ":".join(parts[1:]).strip()
        header[key] = value

    stats = {}
    standard = {}
    coordinates = {}

    # fill in all known stats header fields
    stats["network"] = header["NETWORK"]
    stats["station"] = header["STATION_CODE"]
    stats["channel"] = header["STREAM"]
    stats["location"] = "--"
    stats["delta"] = float(header["SAMPLING_INTERVAL_S"])
    stats["sampling_rate"] = 1 / stats["delta"]
    stats["calib"] = 1.0
    stats["npts"] = int(header["NDATA"])
    stimestr = header["DATE_TIME_FIRST_SAMPLE_YYYYMMDD_HHMMSS"]
    stats["starttime"] = datetime.strptime(stimestr, TIMEFMT)

    # fill in standard fields
    head, tail = os.path.split(filename)
    standard["source_file"] = tail or os.path.basename(head)
    standard["source"] = SRC
    standard["source_format"] = FORMAT
    standard["horizontal_orientation"] = np.nan
    standard["vertical_orientation"] = np.nan
    standard["station_name"] = header["STATION_NAME"]
    try:
        standard["instrument_period"] = 1 / float(header["INSTRUMENTAL_FREQUENCY_HZ"])
    except ValueError:
        standard["instrument_period"] = np.nan
    try:
        standard["instrument_damping"] = 1 / float(header["INSTRUMENTAL_DAMPING"])
    except ValueError:
        standard["instrument_damping"] = np.nan

    ptimestr = header["DATA_TIMESTAMP_YYYYMMDD_HHMMSS"]
    ptime = datetime.strptime(ptimestr, TIMEFMT).strftime(TIMEFMT2)
    standard["process_time"] = ptime
    standard["process_level"] = PROCESS_LEVELS["V1"]
    instr_str = header["INSTRUMENT"]
    parts = instr_str.split("|")
    sensor_str = parts[0].split("=")[1].strip()
    standard["sensor_serial_number"] = ""
    standard["instrument"] = sensor_str
    standard["comments"] = ""
    standard["structure_type"] = ""
    standard["units"] = "cm/s^2"
    standard["units_type"] = "acc"
    standard["instrument_sensitivity"] = np.nan
    standard["volts_to_counts"] = np.nan
    standard["corner_frequency"] = np.nan

    coordinates["latitude"] = float(header["STATION_LATITUDE_DEGREE"])
    coordinates["longitude"] = float(header["STATION_LONGITUDE_DEGREE"])
    coordinates["elevation"] = float(header["STATION_ELEVATION_M"])

    # read in the data
    data = np.genfromtxt(filename, skip_header=TEXT_HDR_ROWS)

    # create a Trace from the data and metadata
    stats["standard"] = standard
    stats["coordinates"] = coordinates
    trace = StationTrace(data.copy(), Stats(stats.copy()))
    response = {"input_units": "counts", "output_units": "cm/s^2"}
    trace.setProvenance("remove_response", response)
    ftype = header["FILTER_TYPE"].capitalize()
    try:
        forder = int(header["FILTER_ORDER"])
    except ValueError:
        forder = 0

    try:
        lowfreq = float(header["LOW_CUT_FREQUENCY_HZ"])
    except ValueError:
        lowfreq = np.nan
    try:
        highfreq = float(header["LOW_CUT_FREQUENCY_HZ"])
    except ValueError:
        highfreq = np.nan
    if not np.isnan(lowfreq) and not np.isnan(lowfreq):
        filter_att = {
            "bandpass_filter": {
                "filter_type": ftype,
                "lower_corner_frequency": lowfreq,
                "higher_corner_frequency": highfreq,
                "filter_order": forder,
            }
        }
        trace.setProvenance("lowpass_filter", filter_att)
    detrend_att = {"detrend": {"detrending_method": "baseline"}}
    if "NOT REMOVED" not in header["BASELINE_CORRECTION"]:
        trace.setProvenance("detrend", detrend_att)
    stream = StationStream(traces=[trace], config=config)
    return [stream]
