import scipy.constants as sp

LOG_FILE = '.gmprocess/logs/gmprocess.log'
CONFIG_FILE = '.gmprocess/config.yml'
LOG_CONFIG_FILE = '.gmprocess/logging.conf'

DEFAULT_CONFIG = {
    'processing_parameters': {
        'amplitude': {
            'min': 10e-7,
            'max': 5e3
        },
        'window': {
            'vmin': 1.0
        },
        'taper': {
            'type': 'hann',
            'max_percentage': 0.05,
            'side': 'both'
        },
        'corners': {
            'get_dynamically': True,
            'sn_ratio': 3.0,
            'max_low_freq': 0.1,
            'min_high_freq': 5.0,
            'default_low_frequency': 0.1,
            'default_high_frequency': 20.0
        },
        'filters': [{
            'type': 'highpass',
            'corners': 4,
            'zerophase': True
        }, {
            'type': 'lowpass',
            'corners': 4,
            'zerophase': True
        }],
        'baseline_correct': True,
    },
    'sm2xml': {
        'imtlist': ['PGA', 'PGV', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)']
    }
}

GAL_TO_PCTG = 1 / sp.g
