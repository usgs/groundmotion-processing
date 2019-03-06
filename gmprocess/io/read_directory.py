"""
Module for methods for reading in directories of data, particularly messy data
from CESMD.
"""

import os
import glob

from gmprocess.io.read import read_data
from gmprocess.io.utils import flatten_directory

EXT_IGNORE = [".gif", ".csv", ".dis", ".abc", ".zip", ".rs2", ".fs1"]


def directory_to_streams(directory):
    """Read in a directory of data to a list of streams.

    Note:
    If the directory only includes files that are readable by this library
    then the task is rather simple. However, often times data directories
    include random subdirectories and/or zip files, which we try to crawl in
    a sensible fashion.

    Args:
        directory (str):
            Directory of ground motion files (streams).

    Returns:
        tuple: (List of obspy streams,
                List of unprocessed files,
                List of errors associated with trying to read unprocessed
                files).
    """

    flatten_directory(directory)

    # -------------------------------------------------------------------------
    # Read streams
    # -------------------------------------------------------------------------
    streams = []
    unprocessed_files = []
    unprocessed_file_errors = []
    for file_path in glob.glob(os.path.join(directory, "*")):
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in EXT_IGNORE:
            try:
                streams += read_data(file_path)
            except Exception as ex:
                unprocessed_files += [file_path]
                unprocessed_file_errors += [ex]

    return streams, unprocessed_files, unprocessed_file_errors


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
