#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pkg_resources

from configobj import ConfigObj
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from schema import Schema, Or, Optional

from gmprocess.utils import constants


CONF_SCHEMA = Schema(
    {
        "user": {"name": str, "email": str},
        "fetchers": {
            Optional("KNETFetcher"): {
                "user": str,
                "password": str,
                "radius": float,
                "dt": float,
                "ddepth": float,
                "dmag": float,
                "restrict_stations": bool,
            },
            Optional("CESMDFetcher"): {
                "email": str,
                "process_type": Or("raw", "processed"),
                "station_type": Or(
                    "Any",
                    "Array",
                    "Ground",
                    "Building",
                    "Bridge",
                    "Dam",
                    "Tunnel",
                    "Warf",
                    "Other",
                ),
                "eq_radius": float,
                "eq_dt": float,
                "station_radius": float,
            },
            Optional("TurkeyFetcher"): {
                "radius": float,
                "dt": float,
                "ddepth": float,
                "dmag": float,
            },
            Optional("FDSNFetcher"): {
                "domain": {
                    "type": Or("circular", "rectangular"),
                    "circular": {
                        "use_epicenter": bool,
                        Optional("latitude"): float,
                        Optional("longitude"): float,
                        "minradius": float,
                        "maxradius": float,
                    },
                    "rectangular": {
                        "minlatitude": float,
                        "maxlatitude": float,
                        "minlongitude": float,
                        "maxlongitude": float,
                    },
                },
                "restrictions": {
                    "time_before": float,
                    "time_after": float,
                    Optional("chunklength_in_sec"): float,
                    Optional("network"): str,
                    Optional("station"): str,
                    Optional("location"): str,
                    Optional("channel"): str,
                    Optional("exclude_networks"): list,
                    Optional("exclude_stations"): list,
                    Optional("reject_channels_with_gaps"): bool,
                    Optional("minimum_length"): float,
                    Optional("sanitize"): bool,
                    Optional("minimum_interstation_distance_in_m"): float,
                    Optional("channel_priorities"): list,
                    Optional("location_priorities"): list,
                },
                Optional("authentication"): dict,
            },
        },
        "read": {
            "metadata_directory": str,
            "resample_rate": float,
            "sac_conversion_factor": float,
            "sac_source": str,
            "use_streamcollection": bool,
            "exclude_patterns": list,
        },
        "windows": {
            "signal_end": {
                "method": str,
                "vmin": float,
                "floor": float,
                "model": str,
                "epsilon": float,
            },
            "window_checks": {
                "do_check": bool,
                "min_noise_duration": float,
                "min_signal_duration": float,
            },
        },
        "processing": list,
        Optional("colocated"): {
            "preference": list,
            Optional("large_dist"): {"preference": list, "mag": list, "dist": list},
        },
        "duplicate": {
            "max_dist_tolerance": float,
            "preference_order": list,
            "process_level_preference": list,
            "format_preference": list,
        },
        "build_report": {"format": "latex"},
        "metrics": {
            "output_imcs": list,
            "output_imts": list,
            "sa": {
                "damping": float,
                "periods": {
                    "start": float,
                    "stop": float,
                    "num": int,
                    "spacing": str,
                    "use_array": bool,
                    "defined_periods": list,
                },
            },
            "fas": {
                "smoothing": str,
                "bandwidth": float,
                "allow_nans": bool,
                "periods": {
                    "start": float,
                    "stop": float,
                    "num": int,
                    "spacing": str,
                    "use_array": bool,
                    "defined_periods": list,
                },
            },
            "duration": {"intervals": list},
        },
        "integration": {
            "frequency": bool,
            "initial": float,
            "demean": bool,
            "taper": {"taper": bool, "type": str, "width": float, "side": str},
        },
        "differentiation": {
            "frequency": bool,
        },
        "pickers": {
            "p_arrival_shift": float,
            Optional("ar"): {
                "f1": float,
                "f2": float,
                "lta_p": float,
                "sta_p": float,
                "lta_s": float,
                "sta_s": float,
                "m_p": int,
                "m_s": int,
                "l_p": float,
                "l_s": float,
                "s_pick": bool,
            },
            Optional("baer"): {
                "tdownmax": float,
                "tupevent": int,
                "thr1": float,
                "thr2": float,
                "preset_len": int,
                "p_dur": float,
            },
            Optional("kalkan"): {
                "period": Or("None", float),
                "damping": float,
                "nbins": Or("None", float),
                "peak_selection": bool,
            },
            Optional("power"): {
                "highpass": float,
                "lowpass": float,
                "order": int,
                "sta": float,
                "sta2": float,
                "lta": float,
                "hanningWindow": float,
                "threshDetect": float,
                "threshDetect2": float,
                "threshRestart": float,
            },
            "travel_time": {"model": str},
        },
    }
)


def update_dict(target, source):
    """Merge values from source dictionary into target dictionary.

    Args:
        target (dict):
            Dictionary to be updated with values from source dictionary.

        source (dict):
            Dictionary with values to be transferred to target dictionary.
    """
    for key, value in source.items():
        if (
            not isinstance(value, dict)
            or key not in target.keys()
            or not isinstance(target[key], dict)
        ):
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


def get_config(config_file=None, section=None, use_default=False):
    """Gets the user defined config and validates it.

    Args:
        config_file:
            Path to config file to use. If None, uses defaults.
        section (str):
            Name of section in the config to extract (i.e., 'fetchers', 'processing',
            'pickers', etc.) If None, whole config is returned.
        use_default (bool):
            Use the default "production" config; this takes precedence  over project
            config settings. Only intended for tutorials/documentation.

    Returns:
        dictionary:
            Configuration parameters.
    Raises:
        IndexError:
            If input section name is not found.
    """
    if use_default:
        data_dir = os.path.abspath(pkg_resources.resource_filename("gmprocess", "data"))
        config_file = os.path.join(data_dir, constants.CONFIG_FILE_PRODUCTION)

    if config_file is None:
        # Try not to let tests interfere with actual system:
        if os.getenv("CALLED_FROM_PYTEST") is None:
            # Not called from pytest -- Is there a local project?
            local_proj = os.path.join(os.getcwd(), constants.PROJ_CONF_DIR)
            local_proj_conf = os.path.join(local_proj, "projects.conf")
            if os.path.isdir(local_proj) and os.path.isfile(local_proj_conf):
                # There's a local project
                config_file = __proj_to_conf_file(local_proj)
            else:
                # Is there a system project?
                sys_proj = constants.PROJECTS_PATH
                sys_proj_conf = os.path.join(sys_proj, "projects.conf")
                if os.path.isdir(sys_proj) and os.path.isfile(sys_proj_conf):
                    config_file = __proj_to_conf_file(sys_proj)
                else:
                    # Fall back on conf file in repository
                    data_dir = os.path.abspath(
                        pkg_resources.resource_filename("gmprocess", "data")
                    )
                    config_file = os.path.join(
                        data_dir, constants.CONFIG_FILE_PRODUCTION
                    )
        else:
            # When called by pytest
            data_dir = os.path.abspath(
                pkg_resources.resource_filename("gmprocess", "data")
            )
            config_file = os.path.join(data_dir, constants.CONFIG_FILE_TEST)

    if not os.path.isfile(config_file):
        fmt = "Missing config file: %s."
        raise OSError(fmt % config_file)
    else:
        with open(config_file, "r", encoding="utf-8") as f:
            yaml = YAML()
            yaml.preserve_quotes = True
            config = yaml.load(f)

    if use_default:
        config["user"] = {"name": "Default", "email": "default@default.comf"}

    CONF_SCHEMA.validate(config)

    if section is not None:
        if section not in config:
            raise IndexError(f"Section {section} not found in config file.")
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
        with open(custom_cfg_file, "rt", encoding="utf-8") as f:
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
    proj_conf_file = os.path.join(path, "projects.conf")
    projects_conf = ConfigObj(proj_conf_file, encoding="utf-8")
    project = projects_conf["project"]
    current_project = projects_conf["projects"][project]
    conf_path = current_project["conf_path"]
    conf_file = os.path.join(conf_path, "config.yml")
    if not os.path.isfile(conf_file):
        conf_file = os.path.join(path, conf_path, "config.yml")
    return conf_file
