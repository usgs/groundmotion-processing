#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for methods for reading in directories of data, particularly messy data
from CESMD.
"""

import os
import glob
import tempfile
import shutil
import logging

from gmprocess.io.read import read_data
from gmprocess.io.utils import flatten_directory

EXT_IGNORE = [".gif", ".csv", ".dis", ".abc", ".zip", ".rs2", ".fs1", ".xml"]


def directory_to_streams(directory, config=None):
    """Read in a directory of data to a list of streams.

    Note:
    If the directory only includes files that are readable by this library
    then the task is rather simple. However, often times data directories
    include random subdirectories and/or zip files, which we try to crawl in
    a sensible fashion.

    Args:
        directory (str):
            Directory of ground motion files (streams).
        config (dict):
            Configuration options.

    Returns:
        tuple: (List of obspy streams,
                List of unprocessed files,
                List of errors associated with trying to read unprocessed
                files).
    """
    # Use a temp dir so that we don't modify data on disk since that may not be
    # expected or desired in all cases. We create the temporary directory in
    # the parent directory, which permits using shutil.copytree to duplicate
    # the data prior to processing.
    intermediate_dir = tempfile.mkdtemp(dir=os.path.dirname(directory))
    temp_dir = os.path.join(intermediate_dir, "directory_to_streams")
    try:
        shutil.copytree(directory, temp_dir)
        flatten_directory(temp_dir)
        # ---------------------------------------------------------------------
        # Read streams
        # ---------------------------------------------------------------------
        streams = []
        unprocessed_files = []
        unprocessed_file_errors = []
        for file_path in glob.glob(os.path.join(temp_dir, "*")):
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()
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
            shutil.rmtree(intermediate_dir)
        except OSError:
            shutil.rmtree(intermediate_dir)

    return streams, unprocessed_files, unprocessed_file_errors


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
