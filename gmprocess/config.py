#!/usr/bin/env python

import os.path
import logging
import yaml

from gmprocess.constants import CONFIG_FILE, PICKER_FILE


def get_config(picker=False):
    """Gets the user defined config and validates it.

    Notes:
        If no config file is present, default parameters are used.

    Args:
        picker (bool):
            If True, returns the config dictionary defined in PICKER_FILE.
            Otherwise, returns the config dictionary defined in CONFIG_FILE.

    Returns:
        dictionary: Configuration parameters.
    """
    if picker:
        file_to_use = PICKER_FILE
    else:
        file_to_use = CONFIG_FILE
    config_file = os.path.join(os.path.expanduser('~'), file_to_use)

    if not os.path.isfile(config_file):
        fmt = ('Missing config file %s, please run gmsetup to install '
               'default config file.')
        logging.info(fmt % config_file)
        config = None
    else:
        with open(config_file, 'r') as f:
            config = yaml.load(f)

    return config
