#!/usr/bin/env python

import os.path
import logging
import yaml

from gmprocess.constants import CONFIG_FILE, PICKER_FILE


def update_dict(target, source):
    """Merge values from source dictionary into target dictionary.

    Args:
        target (dict):
            Dictionary to be updated with values from source dictionary.

        source (dict):
            Dictionary with values to be transferred to target dictionary.
    """
    for key, value in source.items():
        if not isinstance(value, dict) or \
                not key in target.keys() or \
                not isinstance(target[key], dict):
            target[key] = value
        else:
            update_dict(target[key], value)
    return


def merge_dicts(dicts):
    """Merges a list of dictionaries into a new dictionary.

    The order of the dictionaries in the list provides precedence of the
    values, with values from subsequent dictionaries overriding earlier
    ones.

    Args:
        dicts (list of dictionaries):
            List of dictionaries to be merged.

    Returns:
        dictionary: Merged dictionary.
    """
    target = dicts[0].copy()
    for source in dicts[1:]:
        update_dict(target, source)
    return target


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
            config = yaml.load(f, Loader=yaml.FullLoader)

    return config
