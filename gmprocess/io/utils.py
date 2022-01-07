#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import zipfile
import logging

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
        directory (str):
            Directory of ground motion files (streams).

    Returns:
        None.

    """
    # -------------------------------------------------------------------------
    # First walk all the files and unzip until there are no more zip files
    # -------------------------------------------------------------------------
    has_zips = True
    while has_zips:
        has_zips = _walk_and_unzip(directory)

    # -------------------------------------------------------------------------
    # Flatten directoreis by crawling subdirectories and move files up to base
    # directory, renaming them while taking care to avoid any collisions.
    # -------------------------------------------------------------------------
    for dirpath, sub_dirs, files in os.walk(directory, topdown=False):
        if dirpath != directory:
            # Strip out "directory" path from dirpath
            sub_path = dirpath.replace(directory, "")
            split_path = _split_all_path(sub_path)
            split_path = [s for s in split_path if s != os.path.sep]
            sub_str = "_".join(split_path)
            for f in files:
                # Append subdir to file name:
                long_name = f"{sub_str}_{f}"
                src = os.path.join(dirpath, f)
                # I don't think there should ever be duplicates but I'm
                # leaving this here just in case.
                dst = _handle_duplicates(os.path.join(directory, long_name))
                os.rename(src, dst)

        for d in sub_dirs:
            os.rmdir(os.path.join(dirpath, d))


def _walk_and_unzip(directory):
    has_zips = False
    for dirpath, sub_dirs, files in os.walk(directory, topdown=False):
        for f in files:
            full_file = os.path.join(dirpath, f)
            is_zip = False
            try:
                zipfile.ZipFile(full_file, "r")
                is_zip = True
            except BaseException:
                pass
            if is_zip:
                has_zips = True
                base, ext = os.path.splitext(f)
                with zipfile.ZipFile(full_file, "r") as zip:
                    for m in zip.namelist():
                        zip.extract(m, dirpath)
                        src = os.path.join(dirpath, m)
                        new_name = f"{base}_{m.replace(os.path.sep, '_')}"
                        dst = os.path.join(dirpath, new_name)
                        if not os.path.exists(dst):
                            os.rename(src, dst)
                        else:
                            # This should never happen
                            logging.warning(
                                f"While extracting {f}, file {dst} already exists."
                            )
                os.remove(full_file)
    return has_zips


def _split_all_path(path):
    allparts = []
    while True:
        parts = os.path.split(path)
        if parts[0] == path:
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path:
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def _handle_duplicates(target):
    while os.path.exists(target):
        base, ext = os.path.splitext(target)
        target = base + DUPLICATE_MARKER + ext
    return target
