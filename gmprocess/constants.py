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
