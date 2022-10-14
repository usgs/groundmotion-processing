#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import importlib
from collections import OrderedDict
import logging
from pathlib import Path

# third party imports
import numpy as np

from gmprocess.utils.config import get_config

EXCLUDED_MODS = ["__pycache__"]
EXCLUDED_EXTS = [".xml", ".gif", ".csv", ".dis", ".abc", ".zip", ".rs2", ".fs1"]


def read_data(filename, config=None, read_format=None, **kwargs):
    """
    Read strong motion data from a file.

    Args:
        filename (str or pathlib.Path):
            Path to file
        read_format (str):
            Format of file

    Returns:
        list: Sequence of obspy.core.stream.Streams read from file
    """
    filename = Path(filename)

    file_ext = filename.suffix
    if file_ext in EXCLUDED_EXTS:
        raise ValueError(f"Excluded extension: {filename}")
    # Check if file exists
    if not filename.is_file():
        raise OSError(f"Not a file {filename!r}")
    # Get and validate format
    if config is None:
        config = get_config()
    if read_format is None:
        read_format = _get_format(filename, config)
    else:
        read_format = _validate_format(filename, config, read_format.lower())
    # Load reader and read file
    reader = "gmprocess.io." + read_format + ".core"
    reader_module = importlib.import_module(reader)
    read_name = "read_" + read_format
    read_method = getattr(reader_module, read_name)
    streams = read_method(filename, config, **kwargs)
    return streams


def _get_format(filename, config):
    """
    Get the format of the file.

    Args:
        filename (str or pathlib.Path):
            Path to file
        config (dict):
            Dictionary containing configuration.

    Returns:
        string: Format of file.
    """
    # Get the valid formats
    valid_formats = []
    io_directory = Path(__file__).parent

    # Create valid list
    for module in io_directory.iterdir():
        if module.name.find(".") < 0 and module.name not in EXCLUDED_MODS:
            valid_formats += [module.name]

    # Select most likely format to test first; use ordered dict so we can put
    # control order in which modules are moved to the front of the line.
    filename = Path(filename)
    file_ext = filename.suffix
    ext_dict = OrderedDict()
    ext_dict["obspy"] = [".mseed", ".sac"]
    ext_dict["cwb"] = ["dat"]
    ext_dict["smc"] = [".smc"]
    ext_dict["dmg"] = [".raw", ".v1", ".v2"]
    ext_dict["nsmn"] = ["txt"]
    ext_dict["esm"] = [".asc"]
    ext_dict["knet"] = ["ns", "ew", "ud", "ns1", "ew1", "ud1", "ns2", "ew2", "ud2"]
    ext_dict["renadic"] = [".v1", ".v2"]
    ext_dict["bhrc"] = ["v1", "v2"]
    ext_dict["geonet"] = ["v1", "v2", "v1a", "v2a"]
    ext_dict["cosmos"] = ["v0", "v0c", "v1", "v1c", "v1", "v1c", "v2", "v2c"]

    # List of unique extensions, so we can break out of loop.
    unique_exts = [".mseed", ".sac", ".dat", ".smc", ".txt", ".asc", ".raw"]
    unique_exts.extend(ext_dict["knet"])

    for mod, ext_list in ext_dict.items():
        if file_ext.lower() in ext_list:
            valid_formats.insert(0, valid_formats.pop(valid_formats.index(mod)))
            if file_ext.lower() in unique_exts:
                break

    # Test each format
    formats = []
    for valid_format in valid_formats:
        # Create the module and function name from the request
        reader = "gmprocess.io." + valid_format + ".core"
        reader_module = importlib.import_module(reader)
        is_name = "is_" + valid_format
        is_method = getattr(reader_module, is_name)
        if is_method(filename, config):
            formats += [valid_format]

    # Return the format
    formats = np.asarray(formats)
    if len(formats) == 1:
        return formats[0]
    elif len(formats) == 2 and "gmobspy" in formats:
        return formats[formats != "gmobspy"][0]
    elif len(formats) == 0:
        raise Exception(f"No format found for file {filename!r}.")
    else:
        raise Exception(
            "Multiple formats passing: %r. Please retry file %r "
            "with a specified format." % (formats.tolist(), filename)
        )


def _validate_format(filename, config, read_format):
    """
    Check if the specified format is valid. If not, get format.

    Args:
        filename (str):
            Path to file.
        config (dict):
            Dictionary containing configuration.
        read_format (str):
            Format of file

    Returns:
        string: Format of file.
    """
    # Get the valid formats
    valid_formats = []
    io_directory = (Path(__file__).parent / ".." / "io").resolve()
    # Create valid list
    for module in io_directory.iterdir():
        if module.name.find(".") < 0 and module.name not in EXCLUDED_MODS:
            valid_formats += [module]
    # Check for a valid format
    if read_format in valid_formats:
        reader = f"gmprocess.io.{read_format}.core"
        reader_module = importlib.import_module(reader)
        is_name = "is_" + read_format
        is_method = getattr(reader_module, is_name)
    else:
        logging.warning(
            "Not a supported format %r. "
            "Attempting to find a supported format." % read_format
        )
        return _get_format(filename, config)
    # Check that the format passes tests
    if is_method(filename, config):
        return read_format
    else:
        logging.warning(
            "File did not match specified format. "
            "Attempting to find a supported format."
        )
        return _get_format(filename, config)
