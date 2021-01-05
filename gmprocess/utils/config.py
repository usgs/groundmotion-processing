#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
import pkg_resources

from gmprocess.utils.constants import CONFIG_FILE_TEST, CONFIG_FILE_PRODUCTION


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
                key not in target.keys() or \
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


def get_config(config_file=None, section=None):
    """Gets the user defined config and validates it.

    Args:
        config_file:
            Path to config file to use. If None, uses defaults.
        section (str):
            Name of section in the config to extract (i.e., 'fetchers',
            'processing', 'pickers', etc.) If None, whole config is returned.

    Returns:
        dictionary:
            Configuration parameters.
    Raises:
        IndexError:
            If input section name is not found.
    """

    if config_file is None:
        if os.getenv('CALLED_FROM_PYTEST') is not None:
            file_to_use = CONFIG_FILE_TEST
        else:
            file_to_use = CONFIG_FILE_PRODUCTION

        data_dir = os.path.abspath(
            pkg_resources.resource_filename('gmprocess', 'data'))
        config_file = os.path.join(data_dir, file_to_use)

    if not os.path.isfile(config_file):
        fmt = ('Missing config file: %s.')
        raise OSError(fmt % config_file)
    else:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

    if section is not None:
        if section not in config:
            raise IndexError('Section %s not found in config file.' % section)
        else:
            config = config[section]

    return config
