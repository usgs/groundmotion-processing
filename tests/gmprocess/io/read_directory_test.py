
import os

import pkg_resources
import logging

from gmprocess.io.read_directory import directory_to_streams
from gmprocess.logging import setup_logger

setup_logger()


def test_directory_to_streams():
    directory = pkg_resources.resource_filename(
        'gmprocess', os.path.join(
            '..', 'tests', 'data', 'read_directory', 'whittier87'))
    streams, unprocessed_files, unprocessed_file_errors = \
        directory_to_streams(directory)
    assert len(streams) == 4


if __name__ == '__main__':
    test_directory_to_streams()
