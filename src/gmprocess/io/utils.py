#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zipfile
import tarfile
from pathlib import Path
import os

import numpy as np

# local imports
from gmprocess.utils.config import get_config

DUPLICATE_MARKER = "1"


def is_binary(filename):
    """Check if file is binary.

    Args:
        filename (str):
            File to check.

    Returns:
        bool: Is this a binary file?
    """
    # quick check to see if this is a binary or text file
    textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7F})

    def is_binary_string(bytes):
        return bool(bytes.translate(None, textchars))

    return is_binary_string(open(filename, "rb").read(1024))


def is_evenly_spaced(times, rtol=1e-6, atol=1e-8):
    """
    Checks whether times are evenly spaced.

    Args:
        times (array):
            Array of floats of times in seconds.
        rtol (float):
            The relative tolerance parameter. See numpy.allclose.
        atol (float):
            The absolute tolerance parameter. See numpy.allclose.

    Returns:
        bool: True if times are evenly spaced. False otherwise.
    """
    diff_times = np.diff(times)
    return np.all(np.isclose(diff_times[0], diff_times, rtol=rtol, atol=atol))


def resample_uneven_trace(
    trace, times, data, resample_rate=None, method="linear", config=None
):
    """
    Resample unevenly spaced data.

    Args:
        trace (gmprocess.core.stationtrace.StationTrace):
            Trace to resample.
        times (array):
            Array of floats of times in seconds.
        data (array):
            Array of floats of values to be resampled.
        resample_rate (float):
            Resampling rate in Hz.
        method (str):
            Method of resampling. Currently only supported is 'linear'.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        trace (gmprocess.core.stationtrace.StationTrace):
            Resampled trace with updated provenance information.
    """
    npts = len(times)
    duration = times[-1] - times[0]
    nominal_sps = (npts - 1) / duration

    # Load the resampling rate from the config if not provided
    if resample_rate is None:
        if config is None:
            config = get_config()
        resample_rate = config["read"]["resample_rate"]

    new_times = np.arange(times[0], times[-1], 1 / resample_rate)

    # Save max value of original data as a trace parameter
    raw_max = np.max(np.abs(data))

    if method == "linear":
        trace.data = np.interp(new_times, times, data, np.nan, np.nan)
        trace.stats.sampling_rate = resample_rate
        method_str = "Linear interpolation of unevenly spaced samples"
    else:
        raise ValueError("Unsupported method value.")

    trace.setProvenance(
        "resample",
        {
            "record_length": duration,
            "total_no_samples": npts,
            "nominal_sps": nominal_sps,
            "method": method_str,
        },
    )

    trace.setParameter("raw_max", raw_max)
    return trace


def flatten_directory(directory):
    """
    Prepare a messy directory to be read in.

    This is largley motivated by how CESMD distributes data with randomly
    zipped files and subdirectories. This flattens the directory structure
    and prepares it for use with either the gminfo command line program or
    to be read in with teh directory_to_streams method.

    Args:
        directory (str or pathlib.Path):
            Directory of ground motion files (streams).

    Returns:
        None.

    """
    # -------------------------------------------------------------------------
    # First walk all the files and unzip until there are no more zip files
    # -------------------------------------------------------------------------
    if not isinstance(directory, Path):
        directory = Path(directory)

    # Note: need to always resolve here, even if it is already an absolute path. This
    # because /var/ resolves to /private/var/ for some reason that I do not understand
    # and this messes up the path manipulation below.
    directory = directory.resolve()

    has_zips = True
    while has_zips:
        has_zips = _walk_and_unzip(directory)

    # -------------------------------------------------------------------------
    # Flatten directoreis by crawling subdirectories and move files up to base
    # directory, renaming them while trying to avoid any name collisions.
    # -------------------------------------------------------------------------
    for path in _walk(directory):
        # Get portion of path relative "directory" path from dirpath
        sub_path_str = str(path).replace(str(directory), "").strip(os.path.sep)
        sub_path_str = sub_path_str.replace(os.path.sep, "_")
        dst = directory / sub_path_str
        os.rename(path, dst)


def _walk_and_unzip(directory):
    has_zips = False
    for path in _walk(directory):
        is_zip = zipfile.is_zipfile(path)
        is_tar = tarfile.is_tarfile(path)
        if is_zip:
            has_zips = True
            with zipfile.ZipFile(path, "r") as zip:
                for m in zip.namelist():
                    zip.extract(m, str(path.parent))
            path.unlink()
        elif is_tar:
            has_zips = True
            with tarfile.open(path, "r") as tar_file:
                tar_file.extractall(str(path.parent))
            path.unlink()
    return has_zips


def _walk(path):
    for p in path.iterdir():
        if p.is_dir():
            yield from _walk(p)
            continue
        yield p.resolve()
