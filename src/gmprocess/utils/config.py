#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path

from gmprocess.utils import constants
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from schema import Optional, Or, Schema

CONF_SCHEMA = Schema(
    {
        "user": {"name": str, "email": str},
        "fetchers": {
            "KNETFetcher": {
                "user": str,
                "password": str,
                "radius": float,
                "dt": float,
                "ddepth": float,
                "dmag": float,
                "restrict_stations": bool,
                "enabled": bool,
            },
            "CESMDFetcher": {
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
                "enabled": bool,
            },
            "TurkeyFetcher": {
                "radius": float,
                "dt": float,
                "ddepth": float,
                "dmag": float,
                "enabled": bool,
            },
            "FDSNFetcher": {
                "enabled": bool,
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
                "method": Or("model", "velocity", "magnitude", "none"),
                "vmin": float,
                "floor": float,
                "model": str,
                "epsilon": float,
            },
            "window_checks": {
                "enabled": bool,
                "min_noise_duration": float,
                "min_signal_duration": float,
            },
        },
        "processing": list,
        "colocated": {
            "enabled": bool,
            "preference": list,
            "large_dist": {
                "enabled": bool,
                "preference": list,
                "mag": list,
                "dist": list,
            },
        },
        "duplicate": {
            "max_dist_tolerance": float,
            "preference_order": list,
            "process_level_preference": list,
            "format_preference": list,
        },
        "build_report": {"enabled": True, "format": "latex"},
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
            "ar": {
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
            "baer": {
                "tdownmax": float,
                "tupevent": int,
                "thr1": float,
                "thr2": float,
                "preset_len": int,
                "p_dur": float,
            },
            "kalkan": {
                "period": Or("None", float),
                "damping": float,
                "nbins": Or("None", float),
                "peak_selection": bool,
            },
            "power": {
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


def get_config(config_path=None):
    """Gets the user defined config and validates it.

    Args:
        config_path:
            Path to directory containing config files to use. If None, uses defaults.

    Returns:
        dictionary:
            Configuration parameters.
    Raises:
        IndexError:
            If input section name is not found.
    """

    # Read in default config from the repository
    data_dir = Path(__file__).parent / ".." / "data"
    default_config_file = os.path.join(data_dir, constants.CONFIG_FILE_PRODUCTION)
    if not os.path.isfile(default_config_file):
        fmt = "Missing config file: %s."
        raise OSError(fmt % default_config_file)
    else:
        with open(default_config_file, "r", encoding="utf-8") as f:
            yaml = YAML()
            yaml.preserve_quotes = True
            default_config = yaml.load(f)
    # Add in fake user info so validation succeeds
    default_config["user"] = {"name": "NA", "email": "not@provided.com"}
    CONF_SCHEMA.validate(default_config)

    if config_path is None:
        return default_config
    else:
        config = __conf_path_to_config(config_path, default_config)

        return config


def update_config(custom_cfg_file, default_cfg):
    """Merge custom config with default.

    Args:
        custom_cfg_file (str):
            Path to custom config.
        default_cfg (dict):
            Default config file to be updated.

    Returns:
        dict: Merged config dictionary.

    """

    if not os.path.isfile(custom_cfg_file):
        return default_cfg
    try:
        with open(custom_cfg_file, "rt", encoding="utf-8") as f:
            yaml = YAML()
            yaml.preserve_quotes = True
            custom_cfg = yaml.load(f)
            update_dict(default_cfg, custom_cfg)
    except YAMLError:
        return None

    return default_cfg


def __conf_path_to_config(config_path, default_config):
    conf_files = Path(config_path).glob("**/*.yml")
    for cf in conf_files:
        default_config = update_config(cf, default_config)
    return default_config
