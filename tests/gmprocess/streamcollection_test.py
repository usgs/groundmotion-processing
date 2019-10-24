#!/usr/bin/env python

import os
import numpy as np
import json
import pkg_resources

from gmprocess.io.read_directory import directory_to_streams
from gmprocess.logging import setup_logger
from gmprocess.streamcollection import StreamCollection

from obspy import UTCDateTime

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

    test_copy = dmg_sc.copy()
    assert test_copy[0][0].stats['standard']['process_level'] == \
        'uncorrected physical units'

    stream1 = test_copy[0]
    test_append = usc_sc.append(stream1)
    assert len(test_append) == 4

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
        dmg_df['H1']['PGA'],
        0.145615,
        atol=1e5)

    # Check the from_traces method
    traces = []
    for st in sc_test:
        for tr in st:
            traces.append(tr)
    sc_test = StreamCollection.from_traces(traces)
    assert len(sc_test) == 1


def test_duplicates():
    datapath = os.path.join('data', 'testdata', 'duplicate_records')
    datadir = pkg_resources.resource_filename('gmprocess', datapath)
    streams = directory_to_streams(datadir)[0]

    sc_bad = StreamCollection(streams=streams, handle_duplicates=False)
    # Check that we begin with having three streams
    assert len(sc_bad) == 3

    sc = StreamCollection(streams=streams, handle_duplicates=True)
    # Check that we now only have two streams in the StreamCollection
    assert len(sc) == 2
    assert len(sc[0]) == 3
    assert len(sc[1]) == 3

    # Check that we kept the 'CE' network and not the 'ZZ' network
    assert sc.select(station='23837')[0][0].stats.network == 'CE'

    # Now try changing the process levels of one of the streams
    for tr in sc_bad.select(network='ZZ')[0]:
        tr.stats.standard.process_level = 'uncorrected physical units'
    for tr in sc_bad.select(network='CE')[0]:
        tr.stats.standard.process_level = 'corrected physical units'

    sc = StreamCollection(streams=sc_bad.streams, handle_duplicates=True)
    # Now, we should have kept the 'ZZ' network and not the 'CE' network
    assert sc.select(station='23837')[0][0].stats.network == 'ZZ'

    # Now change the process preference order to see if we get back the
    # original results
    sc = StreamCollection(streams=sc_bad.streams, handle_duplicates=True,
                          process_level_preference=['V2', 'V1'])
    assert sc.select(station='23837')[0][0].stats.network == 'CE'

    # Check that decreasing the distance tolerance results in streams now being
    # treated as different streams
    sc = StreamCollection(streams=streams, max_dist_tolerance=10,
                          handle_duplicates=True)
    assert len(sc) == 3

    # Change the streams to have the same processing level
    for st in sc_bad:
        for tr in st:
            tr.stats.standard.process_level = 'uncorrected physical units'

    # Try changing the preferred format order
    sc = StreamCollection(streams=sc_bad.streams, handle_duplicates=True,
                          format_preference=['dmg', 'cosmos'])
    assert sc.select(station='23837')[0][0].stats.network == 'ZZ'

    sc = StreamCollection(streams=sc_bad.streams, handle_duplicates=True,
                          format_preference=['cosmos', 'dmg'])
    assert sc.select(station='23837')[0][0].stats.network == 'CE'

    # Set process level and format to be he same
    for st in sc_bad:
        for tr in st:
            tr.stats.standard.source_format = 'cosmos'

    # Check that we keep the CE network due to the bad starttime on ZZ
    sczz = sc_bad.select(station='23837', network='ZZ')
    for st in sczz:
        for tr in st:
            tr.stats.starttime = UTCDateTime(0)
    sc = StreamCollection(streams=sc_bad.streams, handle_duplicates=True)
    assert sc.select(station='23837')[0][0].stats.network == 'CE'

    for tr in sc_bad.select(network='CE')[0]:
        tr.stats.starttime = UTCDateTime(0)
    for tr in sc_bad.select(network='ZZ')[0]:
        tr.stats.starttime = UTCDateTime(2018, 8, 29, 2, 33, 0)

    sc = StreamCollection(streams=sc_bad.streams, handle_duplicates=True)
    assert sc.select(station='23837')[0][0].stats.network == 'ZZ'

    for tr in sc_bad.select(network='ZZ')[0]:
        tr.stats.starttime = UTCDateTime(0)
        tr.trim(endtime=UTCDateTime(5))

    sc = StreamCollection(streams=sc_bad.streams, handle_duplicates=True)
    assert sc.select(station='23837')[0][0].stats.network == 'CE'

    for tr in sc_bad.select(network='CE')[0]:
        tr.trim(endtime=UTCDateTime(2))

    sc = StreamCollection(streams=sc_bad.streams, handle_duplicates=True)
    assert sc.select(station='23837')[0][0].stats.network == 'ZZ'

    for tr in sc_bad.select(network='ZZ')[0]:
        tr.trim(endtime=UTCDateTime(2))
        tr.resample(20)

    sc = StreamCollection(streams=sc_bad.streams, handle_duplicates=True)
    assert sc.select(station='23837')[0][0].stats.network == 'CE'

    for tr in sc_bad.select(network='ZZ')[0]:
        tr.resample(10)

    sc = StreamCollection(streams=sc_bad.streams, handle_duplicates=True)
    assert sc.select(station='23837')[0][0].stats.network == 'CE'


def test_get_status():
    dpath = os.path.join('data', 'testdata', 'status')
    directory = pkg_resources.resource_filename('gmprocess', dpath)
    sc = StreamCollection.from_directory(directory)

    # Manually fail some of the streams
    sc.select(station='BSAP')[0][0].fail('Failure 0')
    sc.select(station='CPE')[0][0].fail('Failure 1')
    sc.select(station='MIKB', instrument='HN')[0][0].fail('Failure 2')
    sc.select(network='PG', station='PSD')[0][0].fail('Failure 3')

    # Test results from 'short', 'long', and 'net
    short = sc.get_status('short')
    assert (short == 1).all()

    long = sc.get_status('long')
    assert long.at['AZ.BSAP.HN'] == 'Failure 0'
    assert long.at['AZ.BZN.HN'] == ''
    assert long.at['AZ.CPE.HN'] == 'Failure 1'
    assert long.at['CI.MIKB.BN'] == ''
    assert long.at['CI.MIKB.HN'] == 'Failure 2'
    assert long.at['CI.PSD.HN'] == ''
    assert long.at['PG.PSD.HN'] == 'Failure 3'

    net = sc.get_status('net')
    assert net.at['AZ', 'number passed'] == 1
    assert net.at['AZ', 'number failed'] == 2
    assert net.at['CI', 'number passed'] == 2
    assert net.at['CI', 'number failed'] == 1
    assert net.at['PG', 'number passed'] == 0
    assert net.at['PG', 'number failed'] == 1


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_StreamCollection()
    test_duplicates()
    test_get_status()
