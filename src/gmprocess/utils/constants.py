#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scipy.constants as sp
import pathlib

DATA_DIR = (pathlib.Path(__file__).parent / ".." / "data").resolve()
TEST_DATA_DIR = (
    pathlib.Path(__file__).parent / ".." / ".." / ".." / "tests" / "data"
).resolve()

PROJ_CONF_DIR = ".gmprocess"
PROJ_CONF_FILE = "projects.conf"
PROJECTS_PATH = (pathlib.Path("~").expanduser() / PROJ_CONF_DIR).resolve()

CONFIG_PATH_TEST = (pathlib.Path("~").expanduser() / "gmptest").resolve()
CONFIG_FILE_PRODUCTION = "config_production.yml"
CONFIG_FILE_TEST = "config_test.yml"
PICKER_FILE = "picker.yml"
MODULE_FILE = "modules.yml"
RUPTURE_FILE = "rupture.json"
GAL_TO_PCTG = 1.0 / sp.g

WORKSPACE_NAME = "workspace.h5"
WORKSPACE_NAME_OLD = "workspace.hdf"


UNITS = {"PGA": r"%g", "PGV": r"cm/s", "SA": r"%g"}

# Converts acceleration units to cm/s/s
# Converts velocity units to cm/s
# Converts displacement units to cm
UNIT_CONVERSIONS = {
    "gal": 1.0,
    "cm/s/s": 1.0,
    "cm/s^2": 1.0,
    "cm/s**2": 1.0,
    "in/s/s": sp.inch * 100.0,
    "cm/s": 1.0,
    "in/s": sp.inch * 100.0,
    "cm": 1.0,
    "in": sp.inch * 100.0,
    "g": sp.g * 100.0,
    "g/10": sp.g * 10.0,
    "g*10": sp.g * 100.0,
    "mg": sp.g / 1000.0,
}

# Define the number of decimals that should be written
# in the output files depending on the column.
# The keys are regular expressions for matching the column names,
# and the values are the string format for the matching columns.
# This is to hopefully account for when we add additional columns to the tables
# in the future.
TABLE_FLOAT_STRING_FORMAT = {
    "samplingrate": "%.0f",
    ".*magnitude$|.*vs30": "%.1f",
    ".*depth|.*elevation|.*dist|GC2.*|backazimuth": "%.2f",
    ".*latitude|.*longitude|.*highpass|.*lowpass|fmin|fmax|f0": "%.5f",
}

# Formats for storing floating point numbers as strings for the
# WaveFormMetrics and StationMetrics XMLs.
METRICS_XML_FLOAT_STRING_FORMAT = {
    "pgm": "%.8g",
    "period": "%.3f",
    "damping": "%.2f",
    "back_azimuth": "%.2f",
    "vs30": "%.2f",
    "distance": "%.2f",
    "duration": "%.8g",
    "sorted_duration": "%.8g",
}

# Default float format when we don't have a preference
DEFAULT_FLOAT_FORMAT = "%.8E"

# Default NaN representation in outputted flatfiles
DEFAULT_NA_REP = "nan"

# Elevation to use for calculating fault distances (m)
ELEVATION_FOR_DISTANCE_CALCS = 0.0

# Event time format
EVENT_TIMEFMT = "%Y-%m-%dT%H:%M:%S.%f"

NON_IMT_COLS = set(
    [
        "EarthquakeId",
        "EarthquakeTime",
        "EarthquakeLatitude",
        "EarthquakeLongitude",
        "EarthquakeDepth",
        "EarthquakeMagnitude",
        "EarthquakeMagnitudeType",
        "Network",
        "DataProvider",
        "StationCode",
        "StationID",
        "StationDescription",
        "StationLatitude",
        "StationLongitude",
        "StationElevation",
        "SamplingRate",
        "EpicentralDistance",
        "HypocentralDistance",
        "H1Lowpass",
        "H1Highpass",
        "H2Lowpass",
        "H2Highpass",
        "SourceFile",
    ]
)

COMPONENTS = {
    "ROTD50.0": ["SA", "PGA", "PGV"],
    "GREATER_OF_TWO_HORIZONTALS": ["SA", "PGA", "PGV"],
    "QUADRATIC_MEAN": ["FAS"],
    "GEOMETRIC_MEAN": ["FAS"],
    "ARITHMETIC_MEAN": ["FAS"],
    "CHANNELS": ["SA", "PGA", "PGV", "DURATION", "SORTED_DURATION", "ARIAS"],
}
