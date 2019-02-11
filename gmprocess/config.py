#!/usr/bin/env python

import os.path
import logging
import pkg_resources
from configobj import ConfigObj
from validate import Validator

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
    else:
        val = Validator()
        spec_file = pkg_resources.resource_filename(
            'gmprocess', 'data/gmprocess_spec.conf')
        config = ConfigObj(config_file, configspec=spec_file)
        config.validate(val)

    return config
