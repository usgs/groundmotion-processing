#!/usr/bin/env python

import os
import numpy as np
import json
import pkg_resources
import logging

from gmprocess.io.read_directory import directory_to_streams
from gmprocess.logging import setup_logger
from gmprocess.streamcollection import StreamCollection

setup_logger()


def test_StreamCollection():

    # read usc data
    dpath = os.path.join('data', 'testdata', 'usc', 'ci3144585')
    directory = pkg_resources.resource_filename('gmprocess', dpath)
    usc_streams, unprocessed_files, unprocessed_file_errors = \
        directory_to_streams(directory)
    assert len(usc_streams) == 7

    usc_sc = StreamCollection(usc_streams)

    # Use print method
    print(usc_sc)

    # Use len method
    assert len(usc_sc) == 3

    # Use nonzero method
    assert bool(usc_sc)

    # Slice
    lengths = [
        len(usc_sc[0]),
        len(usc_sc[1]),
        len(usc_sc[2])
    ]
    sort_lengths = np.sort(lengths)
    assert sort_lengths[0] == 1
    assert sort_lengths[1] == 3
    assert sort_lengths[2] == 3

    # read dmg data
    dpath = os.path.join('data', 'testdata', 'dmg', 'ci3144585')
    directory = pkg_resources.resource_filename('gmprocess', dpath)
    dmg_streams, unprocessed_files, unprocessed_file_errors = \
        directory_to_streams(directory)
    assert len(dmg_streams) == 1

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

    test_copy = dmg_sc.copy()
    assert test_copy[0][0].stats['standard']['process_level'] == \
        'corrected physical units'

    # Appending dmg should not add to length because of the
    # overwriting of the station/network above
    stream1 = test_copy[0]
    test_append = usc_sc.append(stream1)
    assert len(test_append) == 3

    # Change back to unique values for station/network
    for tr in dmg_sc[0]:
        tr.stats['network'] = 'LALALA'
        tr.stats['station'] = '575757'
    stream2 = dmg_sc[0]
    test_append = usc_sc.append(stream2)
    assert len(test_append) == 4

    # Check the from_directory method
    sc_test = StreamCollection.from_directory(directory)
    assert len(sc_test) == 1

    # Test to_dataframe
    jsonfile = os.path.join(directory, 'event.json')
    with open(jsonfile, 'rt') as f:
        origin = json.load(f)
    dmg_df = sc_test.to_dataframe(origin)
    np.testing.assert_allclose(
        dmg_df['HN1']['PGA'],
        0.145615,
        atol=1e5)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_StreamCollection()
