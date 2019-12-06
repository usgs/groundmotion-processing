import scipy.constants as sp

CONFIG_FILE = 'config.yml'
PICKER_FILE = 'picker.yml'
MODULE_FILE = 'modules.yml'
GAL_TO_PCTG = 1 / sp.g

# Converts acceleration units to cm/s/s
# Converts velocity units to cm/s
# Converts displacement units to cm
UNIT_CONVERSIONS = {
    'gal': 1,
    'cm/s/s': 1,
    'in/s/s': sp.inch*100,
    'cm/s': 1,
    'in/s': sp.inch*100,
    'cm': 1,
    'in': sp.inch*100,
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
# in the future (such as RuptureDistance, e.g.)
# Note: once Vs30 and back azimuth columns are automatically generated,
# they will need to be added to this dictionary
#   - Vs30: 1 decimal
#   - Back azimuth: 2 decimals
TABLE_FLOAT_STRING_FORMAT = {
    '.*latitude|.*longitude': '%.5f',
    '.*depth': '%.2f',
    '.*magnitude$': '%.1f',
    '.*elevation': '%.2f',
    'samplingrate': '%.0f',
    '.*dist': '%.2f',
    '.*highpass|.*lowpass|fmin|fmax|f0': '%.5f',
}

# Default float format when we don't have a preference
DEFAULT_FLOAT_FORMAT = '%.8E'
