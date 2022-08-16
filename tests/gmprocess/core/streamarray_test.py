#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from gmprocess.io.read_directory import directory_to_streams
from gmprocess.utils.logging import setup_logger
from gmprocess.utils.constants import TEST_DATA_DIR
from gmprocess.core.streamarray import StreamArray

setup_logger()


def test_StreamArray():

    # read usc data
    directory = TEST_DATA_DIR / "usc" / "ci3144585"
    usc_streams, _, _ = directory_to_streams(directory)
    assert len(usc_streams) == 7

    usc_sa = StreamArray(usc_streams)

    # Use print method
    print(usc_sa)
    usc_sa.describe()

    # Use len method
    assert len(usc_sa) == 7

    # Use nonzero method
    assert bool(usc_sa)

    # read dmg data
    directory = TEST_DATA_DIR / "dmg" / "ci3144585"
    dmg_streams, unprocessed_files, unprocessed_file_errors = directory_to_streams(
        directory
    )
    assert len(dmg_streams) == 1

    dmg_sa = StreamArray(dmg_streams)
    dmg_sa.describe()

    # Has 3 streams
    assert len(dmg_sa) == 3


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_StreamArray()
