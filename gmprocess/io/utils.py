import os
import zipfile
import logging

import numpy as np

# local imports
from gmprocess.config import get_config

CONFIG = get_config()
DUPLICATE_MARKER = '1'


def is_evenly_spaced(times, decimal_tolerance):
    """
    Checks whether times are evenly spaced.

    Args:
        times (array):
            Array of floats of times in seconds.
        decimal_tolerance (int):
            Decimal tolerance for testing equality of time deltas.

    Returns:
        bool: True if times are evenly spaced. False otherwise.
    """
    diffs = np.diff(times).round(decimals=decimal_tolerance)
    if len(np.unique(diffs)) > 1:
        return False
    else:
        return True


def resample_uneven_trace(trace, times, data, resample_rate=None,
                          method='linear'):
    """
    Resample unevenly spaced data.

    Args:
        trace (gmprocess.stationtrace.StationTrace):
            Trace to resample.
        times (array):
            Array of floats of times in seconds.
        data (array):
            Array of floats of values to be resampled.
        resample_rate (float):
            Resampling rate in Hz.
        method (str):
            Method of resampling. Currently only supported is 'linear'.

    Returns:
        trace (gmprocess.stationtrace.StationTrace):
            Resampled trace with updated provenance information.
    """
    npts = len(times)
    duration = times[-1] - times[0]
    nominal_sps = (npts - 1) / duration

    # Load the resampling rate from the config if not provided
    if resample_rate is None:
        resample_rate = CONFIG['read']['resample_rate']

    new_times = np.arange(times[0], times[-1], 1 / resample_rate)

    if method == 'linear':
        trace.data = np.interp(new_times, times, data, np.nan, np.nan)
        trace.stats.sampling_rate = resample_rate
        method_str = 'Linear interpolation of unevenly spaced samples'
    else:
        raise ValueError('Unsupported method value.')

    trace.setProvenance('resample', {'record_length': duration,
                                     'total_no_samples': npts,
                                     'nominal_sps': nominal_sps,
                                     'method': method_str})

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
    # Flatten directoreis by crawling subdirectories and move files up to base
    # directory, renaming them while taking care to avoid any collisions.
    # -------------------------------------------------------------------------
    for dirpath, sub_dirs, files in os.walk(directory, topdown=False):
        if dirpath != directory:
            # Strip out "directory" path from dirpath
            sub_path = dirpath.replace(directory, '')
            split_path = _split_all_path(sub_path)
            split_path = [s for s in split_path if s != os.path.sep]
            sub_str = '_'.join(split_path)
            for f in files:
                # Append subdir to file name:
                long_name = '%s_%s' % (sub_str, f)
                src = os.path.join(dirpath, f)
                # I don't think there should ever be duplicates but I'm
                # leaving this here just in case.
                dst = _handle_duplicates(
                    os.path.join(directory, long_name))
                os.rename(src, dst)

        for d in sub_dirs:
            os.rmdir(os.path.join(dirpath, d))

    # -------------------------------------------------------------------------
    # Take care of any zip files and extract, trying to ensure that no files
    # get overwritten.
    # -------------------------------------------------------------------------
    all_files = [os.path.join(directory, f) for f in os.listdir(directory)]
    for f in all_files:
        if zipfile.is_zipfile(f):
            # Grab base of file name -- to be used later when appended to
            # the extracted file.
            base, ext = os.path.splitext(f)
            logging.debug('Extracting %s...' % f)
            with zipfile.ZipFile(f, 'r') as zip:
                for m in zip.namelist():
                    zip.extract(m, directory)
                    if base not in m:
                        src = os.path.join(directory, m)
                        new_name = '%s_%s' % (base, m)
                        dst = os.path.join(directory, new_name)
                        if not os.path.exists(dst):
                            os.rename(src, dst)
                        else:
                            logging.warning(
                                'While extracting %s, file %s already exists.'
                                % (f, dst))


def _split_all_path(path):
    allparts = []
    while 1:
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
