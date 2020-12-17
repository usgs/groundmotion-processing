import scipy.constants as sp

CONFIG_FILE_TEST = 'config_test.yml'
CONFIG_FILE_PRODUCTION = 'config_production.yml'
PICKER_FILE = 'picker.yml'
MODULE_FILE = 'modules.yml'
RUPTURE_FILE = 'rupture.json'
GAL_TO_PCTG = 1 / sp.g

# Converts acceleration units to cm/s/s
# Converts velocity units to cm/s
# Converts displacement units to cm
UNIT_CONVERSIONS = {
    'gal': 1,
    'cm/s/s': 1,
    'in/s/s': sp.inch * 100,
    'cm/s': 1,
    'in/s': sp.inch * 100,
    'cm': 1,
    'in': sp.inch * 100,
    'g': sp.g * 100,
    'g/10': sp.g * 10,
    'g*10': sp.g * 100,
    'mg': sp.g / 1000
}

# Define the number of decimals that should be written
# in the output files depending on the column.
# The keys are regular expressions for matching the column names,
# and the values are the string format for the matching columns.
# This is to hopefully account for when we add additional columns to the tables
# in the future.
TABLE_FLOAT_STRING_FORMAT = {
    'samplingrate': '%.0f',
    '.*magnitude$|.*vs30': '%.1f',
    '.*depth|.*elevation|.*dist|GC2.*|backazimuth': '%.2f',
    '.*latitude|.*longitude|.*highpass|.*lowpass|fmin|fmax|f0': '%.5f'
}

# Formats for storing floating point numbers as strings for the
# WaveFormMetrics and StationMetrics XMLs.
METRICS_XML_FLOAT_STRING_FORMAT = {
    'pgm': '%.8g',
    'period': '%.3f',
    'damping': '%.2f',
    'back_azimuth': '%.2f',
    'vs30': '%.2f',
    'distance': '%.2f'
}

# Default float format when we don't have a preference
DEFAULT_FLOAT_FORMAT = '%.8E'

# Default NaN representation in outputted flatfiles
DEFAULT_NA_REP = 'nan'

# Elevation to use for calculating fault distances (m)
ELEVATION_FOR_DISTANCE_CALCS = 0.0
