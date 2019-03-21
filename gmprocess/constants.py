import scipy.constants as sp

CONFIG_FILE = '.gmprocess/config.yml'
PICKER_FILE = '.gmprocess/picker.yml'
GAL_TO_PCTG = 1 / sp.g

# Converts acceleration units to cm/s/s
# Converts velocity units to cm/s
# Converts displacement units to cm
UNIT_CONVERSIONS = {
    'gal': 1,
    'cm/s/s': 1,
    'in/s/s': 2.54,
    'cm/s': 1,
    'in/s': 2.54,
    'cm': 1,
    'in': 2.54,
    'g': sp.g * 100,
    'g/10': sp.g * 100,
    'g*10': sp.g * 10,
    'mg': sp.g / 1000
}
