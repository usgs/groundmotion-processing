#!/usr/bin/env python

import os.path
import logging
import yaml

from gmprocess.constants import CONFIG_FILE


def get_config():
    """Gets the user defined config and validates it.

    Notes:
        If no config file is present, default parameters are used.

    Returns:
        dictionary: Configuration parameters.
    """
    config_file = os.path.join(os.path.expanduser('~'), CONFIG_FILE)
    if not os.path.isfile(config_file):
        fmt = ('Missing config file %s, please run gmsetup to install '
               'default config file.')
        logging.info(fmt % config_file)
        config = None
    else:
        with open(config_file, 'r') as f:
            config = yaml.load(f)

    return config
