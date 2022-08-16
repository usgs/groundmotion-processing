#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import glob

from gmprocess.utils.base_utils import read_event_json_files
from gmprocess.utils.constants import TEST_DATA_DIR


def read_data_dir(file_format, eventid, files=None):
    """Read desired data files and event dictionary from test directory.

    Args:
        file_format (str):
            Name of desired data format (smc, usc, etc.)
        eventid (str):
            ComCat or other event ID (should exist as a folder)
        files (variable):
            This is either:
                - None This is a flag to retrieve all of the files for an
                  event.
                - regex A regex string that glob can handle (*.dat, AO*.*,
                  etc.)
                - list List of specific files that should be returned.

    Returns:
        tuple:
            - List of data files.
            - Event dictionary.
    """
    eventdir = os.path.join(TEST_DATA_DIR, file_format, eventid)
    if not os.path.isdir(eventdir):
        return (None, None)
    datafiles = []
    if files is None:
        allfiles = os.listdir(eventdir)
        allfiles.remove("event.json")
        for dfile in allfiles:
            datafile = os.path.join(eventdir, dfile)
            datafiles.append(datafile)
    elif isinstance(files, str):  # regex
        datafiles = glob.glob(os.path.join(eventdir, files))
    else:  # this is just a list of filenames
        for tfile in files:
            fullfile = os.path.join(eventdir, tfile)
            if os.path.isfile(fullfile):
                datafiles.append(fullfile)

    # read the event.json file
    jsonfile = os.path.join(eventdir, "event.json")
    if not os.path.isfile(jsonfile):
        event = None
    event = read_event_json_files([jsonfile])[0]

    return (datafiles, event)
