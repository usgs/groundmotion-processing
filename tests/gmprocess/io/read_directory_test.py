
import os.path

import pkg_resources
import logging

from gmprocess.io.read_directory import directory_to_streams
from gmprocess.logging import setup_logger

setup_logger()


def test_directory_to_streams():
    dpath = os.path.join('data', 'testdata', 'read_directory', 'whittier87')
    directory = pkg_resources.resource_filename('gmprocess', dpath)

    streams, unprocessed_files, unprocessed_file_errors = directory_to_streams(
        directory)
    assert len(streams) == 7


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_directory_to_streams()
