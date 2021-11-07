#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pkg_resources

from configobj import ConfigObj
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from gmprocess.utils import constants


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
        # Try not to let tests interfere with actual system:
        if os.getenv('CALLED_FROM_PYTEST') is None:
            # Not called from pytest -- Is there a local project?
            local_proj = os.path.join(os.getcwd(), constants.PROJ_CONF_DIR)
            local_proj_conf = os.path.join(local_proj, 'projects.conf')
            if os.path.isdir(local_proj) and os.path.isfile(local_proj_conf):
                # There's a local project
                config_file = __proj_to_conf_file(local_proj)
            else:
                # Is there a system project?
                sys_proj = constants.PROJECTS_PATH
                sys_proj_conf = os.path.join(sys_proj, 'projects.conf')
                if os.path.isdir(sys_proj) and os.path.isfile(sys_proj_conf):
                    config_file = __proj_to_conf_file(sys_proj)
                else:
                    # Fall back on conf file in repository
                    data_dir = os.path.abspath(
                        pkg_resources.resource_filename('gmprocess', 'data'))
                    config_file = os.path.join(
                        data_dir, constants.CONFIG_FILE_PRODUCTION)
        else:
            # When called by pytest
            data_dir = os.path.abspath(
                pkg_resources.resource_filename('gmprocess', 'data'))
            config_file = os.path.join(data_dir, constants.CONFIG_FILE_TEST)

    if not os.path.isfile(config_file):
        fmt = ('Missing config file: %s.')
        raise OSError(fmt % config_file)
    else:
        with open(config_file, 'r', encoding='utf-8') as f:
            yaml = YAML()
            yaml.preserve_quotes = True
            config = yaml.load(f)

    if section is not None:
        if section not in config:
            raise IndexError('Section %s not found in config file.' % section)
        else:
            config = config[section]

    return config


def update_config(custom_cfg_file):
    """Merge custom config with default.

    Args:
        custom_cfg_file (str):
            Path to custom config.

    Returns:
        dict: Merged config dictionary.

    """
    config = get_config()

    if not os.path.isfile(custom_cfg_file):
        return config
    try:
        with open(custom_cfg_file, 'rt', encoding='utf-8') as f:
            yaml = YAML()
            yaml.preserve_quotes = True
            custom_cfg = yaml.load(f)
            update_dict(config, custom_cfg)
    except YAMLError:
        return None

    return config


def __proj_to_conf_file(path):
    # We are switching from absolute to relative paths in this conf file. For
    # backward compatibility, we're going to try to support both absolute and
    # relative paths, which is why we need this "try" block to first assume
    # an absolute path and if the conf does not exist then try a relative path.
    proj_conf_file = os.path.join(path, 'projects.conf')
    projects_conf = ConfigObj(proj_conf_file, encoding='utf-8')
    project = projects_conf['project']
    current_project = projects_conf['projects'][project]
    conf_path = current_project['conf_path']
    conf_file = os.path.join(conf_path, 'config.yml')
    if not os.path.isfile(conf_file):
        conf_file = os.path.join(path, conf_path, 'config.yml')
    return conf_file
