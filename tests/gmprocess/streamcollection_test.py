import os
import shutil
import tempfile

import pkg_resources
import logging

from gmprocess.io.read_directory import directory_to_streams
from gmprocess.logging import setup_logger
from gmprocess.streamcollection import StreamCollection

setup_logger()


def test_StreamCollection():

    directory = pkg_resources.resource_filename(
        'gmprocess', os.path.join(
            '..', 'tests', 'data', 'usc', 'ci3144585'))
    temp_dir = os.path.join(tempfile.mkdtemp(), 'test')
    try:
        shutil.copytree(directory, temp_dir)
        streams, unprocessed_files, unprocessed_file_errors = \
            directory_to_streams(temp_dir)
        assert len(streams) == 7
    except:
        raise Exception('test_directory_to_streams Failed.')
    finally:
        shutil.rmtree(temp_dir)

    sc = StreamCollection(streams)


if __name__ == '__main__':
    test_StreamCollection()
