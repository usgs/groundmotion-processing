#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for methods for reading in directories of data, particularly messy data
from CESMD.
"""

import tempfile
import shutil
import logging
from pathlib import Path

from gmprocess.io.read import read_data
from gmprocess.io.utils import flatten_directory
from gmprocess.io.utils import _walk

EXT_IGNORE = [".gif", ".csv", ".dis", ".abc", ".zip", ".rs2", ".fs1", ".xml"]


def directory_to_streams(directory, config=None):
    """Read in a directory of data to a list of streams.

    Note:
    If the directory only includes files that are readable by this library
    then the task is rather simple. However, often times data directories
    include random subdirectories and/or zip files, which we try to crawl in
    a sensible fashion.

    Args:
        directory (str or pathlib.Path):
            Directory of ground motion files (streams).
        config (dict):
            Configuration options.

    Returns:
        tuple: (List of obspy streams,
                List of unprocessed files,
                List of errors associated with trying to read unprocessed
                files).
    """
    directory = Path(directory)
    # Use a temp dir so that we don't modify data on disk since that may not be
    # expected or desired in all cases.
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        target_dir = tmp_dir / "directory_to_streams"
        shutil.copytree(directory, target_dir)
        flatten_directory(target_dir)
        # ---------------------------------------------------------------------
        # Read streams
        # ---------------------------------------------------------------------
        streams = []
        unprocessed_files = []
        unprocessed_file_errors = []
        for file_path in _walk(target_dir):
            file_name = file_path.name
            file_ext = file_path.suffix.lower()
            if file_ext not in EXT_IGNORE:
                try:
                    logging.debug(f"Attempting to read: {file_path}")
                    streams += read_data(file_path, config=config)
                except BaseException as ex:
                    logging.info(f"Failed to read file: {file_name}")
                    unprocessed_files += [file_path]
                    unprocessed_file_errors += [ex]

    except BaseException as e:
        raise e
    finally:
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except OSError:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    return streams, unprocessed_files, unprocessed_file_errors
