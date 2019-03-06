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

    # read usc data
    directory = pkg_resources.resource_filename(
        'gmprocess', os.path.join(
            '..', 'tests', 'data', 'usc', 'ci3144585'))
    temp_dir = os.path.join(tempfile.mkdtemp(), 'test')
    try:
        shutil.copytree(directory, temp_dir)
        usc_streams, unprocessed_files, unprocessed_file_errors = \
            directory_to_streams(temp_dir)
        assert len(usc_streams) == 7
    except:
        raise Exception('test_directory_to_streams Failed.')
    finally:
        shutil.rmtree(temp_dir)

    usc_sc = StreamCollection(usc_streams)

    # Use len method
    assert len(usc_sc) == 3

    # Use nonzero method
    assert bool(usc_sc)

    # Slice
    assert len(usc_sc[0]) == 1
    assert len(usc_sc[1]) == 3

    # read dmg data
    directory = pkg_resources.resource_filename(
        'gmprocess', os.path.join(
            '..', 'tests', 'data', 'dmg', 'ci3144585'))
    temp_dir = os.path.join(tempfile.mkdtemp(), 'test')
    try:
        shutil.copytree(directory, temp_dir)
        dmg_streams, unprocessed_files, unprocessed_file_errors = \
            directory_to_streams(temp_dir)
        assert len(dmg_streams) == 1
    except:
        raise Exception('test_directory_to_streams Failed.')
    finally:
        shutil.rmtree(temp_dir)

    dmg_sc = StreamCollection(dmg_streams)

    # Has one station
    assert len(dmg_sc) == 1
    # With 3 channels
    assert len(dmg_sc[0]) == 3

    # So this should have 4 stations
    test1 = dmg_sc + usc_sc
    assert len(test1) == 4

    # Overwrite the dmg station and network to force it to be
    # a duplicate of one of the stations in usc_sc to check if
    # validation works with these addition methods
    for tr in dmg_sc[0]:
        tr.stats['network'] = 'LA'
        tr.stats['station'] = '57'

    test3 = dmg_sc + usc_sc
    assert len(test3) == 3
    # usc_sc has 1 channel for station 57 and the modified
    # dmg_sc has 3 channels so the combined StreamCollection
    # should have 4
    assert len(test3[0]) == 4


if __name__ == '__main__':
    test_StreamCollection()
