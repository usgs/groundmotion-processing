"""
Module for methods for reading in directories of data, particularly messy data
from CESMD.
"""

import os
import logging
import zipfile
import glob

from gmprocess.io.read import read_data


DUPLICATE_MARKER = '1'
EXT_IGNORE = [".gif", ".csv", ".dis", ".abc", ".zip", ".rs2", ".fs1"]
# V3 is sometimes response spectra, sometimes time series so don't
# include it on this list.


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
        List of obspy streams.
    """
    # logging.warning("This method is not yet functional. Exiting.")
    # sys.exit(1)

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

    return streams


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
