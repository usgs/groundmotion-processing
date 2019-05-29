#!/usr/bin/env python

# stdlib imports
import glob
import os

# third party imports
import numpy as np
from obspy.core.event import Origin
import pandas as pd
import pkg_resources

# Local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.io.knet.core import read_knet
from gmprocess.io.read import read_data
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.processing import process_streams
from gmprocess.stream import directory_to_dataframe, streams_to_dataframe
from gmprocess.streamcollection import StreamCollection
from gmprocess.io.test_utils import read_data_dir


def test():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?

    # Test for channel grouping with three unique channels
    streams = []
    # datadir = os.path.join(homedir, '..', 'data', 'knet', 'us2000cnnl')
    datafiles, origin = read_data_dir('knet', 'us2000cnnl',
                                      'AOM0031801241951*')
    for datafile in datafiles:
        streams += read_knet(datafile)
    grouped_streams = StreamCollection(streams)
    assert len(grouped_streams) == 1
    assert grouped_streams[0].count() == 3

    # Test for channel grouping with more file types
    datafiles, origin = read_data_dir('geonet',
                                      'us1000778i',
                                      '20161113_110313_THZ_20.V2A')
    datafile = datafiles[0]
    streams += read_geonet(datafile)
    grouped_streams = StreamCollection(streams)
    assert len(grouped_streams) == 2
    assert grouped_streams[0].count() == 3
    assert grouped_streams[1].count() == 3

    # Test for warning for one channel streams
    datafiles, origin = read_data_dir(
        'knet', 'us2000cnnl', 'AOM0071801241951.UD')
    datafile = datafiles[0]
    streams += read_knet(datafile)

    grouped_streams = StreamCollection(streams)
#    assert "One channel stream:" in logstream.getvalue()

    assert len(grouped_streams) == 3
    assert grouped_streams[0].count() == 3
    assert grouped_streams[1].count() == 3
    assert grouped_streams[2].count() == 1


def test_grouping():
    cwb_files, _ = read_data_dir('cwb', 'us1000chhc')
    cwb_streams = []
    for filename in cwb_files:
        cwb_streams += read_data(filename)
    cwb_streams = StreamCollection(cwb_streams)
    assert len(cwb_streams) == 5
    for stream in cwb_streams:
        assert len(stream) == 3

    # dmg
    dpath = os.path.join('data', 'testdata', 'dmg')
    dmg_path = pkg_resources.resource_filename('gmprocess', dpath)
    dmg_files = []
    for (path, dirs, files) in os.walk(dmg_path):
        for file in files:
            if file.endswith('V2'):
                fullfile = os.path.join(path, file)
                dmg_files.append(fullfile)

    dmg_streams = []
    for filename in dmg_files:
        if (not os.path.basename(filename).startswith('Bad') and
                not os.path.basename(filename).startswith('CE58667')):
            dmg_streams += read_data(filename)
    dmg_streams = StreamCollection(dmg_streams)
    assert len(dmg_streams) == 2
    for stream in dmg_streams:
        assert len(stream) == 3

    # geonet
    geonet_files, _ = read_data_dir('geonet', 'us1000778i', '*.V1A')
    geonet_streams = []
    for filename in geonet_files:
        geonet_streams += read_data(filename)
    geonet_streams = StreamCollection(geonet_streams)
    assert len(geonet_streams) == 3
    for stream in geonet_streams:
        assert len(stream) == 3
        assert len(stream.select(station=stream[0].stats.station)) == 3
        level = stream[0].stats.standard.process_level
        for trace in stream:
            assert trace.stats.standard.process_level == level

    # kiknet
    kiknet_files, _ = read_data_dir('kiknet', 'usp000a1b0')
    kiknet_streams = []
    for filename in kiknet_files:
        kiknet_streams += read_data(filename)
    kiknet_streams = StreamCollection(kiknet_streams)
    assert len(kiknet_streams) == 1
    for stream in kiknet_streams:
        assert len(stream) == 3
        assert len(stream.select(station=stream[0].stats.station)) == 3

    # knet
    knet_files, _ = read_data_dir('knet', 'us2000cnnl')
    knet_streams = []
    for filename in knet_files:
        knet_streams += read_data(filename)
    knet_streams = StreamCollection(knet_streams)
    assert len(knet_streams) == 9
    for stream in knet_streams:
        assert len(stream) == 3
        assert len(stream.select(station=stream[0].stats.station)) == 3
        pl = stream[0].stats.standard.process_level
        for trace in stream:
            assert trace.stats.standard.process_level == pl

    # smc
    smc_files, _ = read_data_dir('smc', 'nc216859', '0111*')
    smc_streams = []
    for filename in smc_files:
        smc_streams += read_data(filename, any_structure=True)
    smc_streams = StreamCollection(smc_streams)
    assert len(smc_streams) == 1
    for stream in smc_streams:
        if stream[0].stats.station == 'DVD0':
            assert len(stream) == 1
            assert len(stream.select(station=stream[0].stats.station)) == 1
        elif stream[0].stats.location == '01':
            assert len(stream) == 2
            assert len(stream.select(station=stream[0].stats.station)) == 2
        else:
            assert len(stream) == 3
            assert len(stream.select(station=stream[0].stats.station)) == 3

    # usc
    usc_files, _ = read_data_dir('usc', 'ci3144585')
    usc_streams = []
    for filename in usc_files:
        if os.path.basename(filename) != '017m30bt.s0a':
            usc_streams += read_data(filename)
    usc_streams = StreamCollection(usc_streams)
    assert len(usc_streams) == 3
    for stream in usc_streams:
        if stream[0].stats.station == '57':
            assert len(stream) == 1
        else:
            assert len(stream) == 3


def test_to_dataframe():
    cwb_files, event = read_data_dir('geonet', 'nz2018p115908')
    st = read_data(cwb_files[0])[0]
    df1 = streams_to_dataframe([st, st], event=event)
    np.testing.assert_array_equal(df1.STATION.tolist(), ['WPWS', 'WPWS'])
    np.testing.assert_array_equal(df1.NAME.tolist(),
                                  ['Waipawa_District_Council', 'Waipawa_District_Council'])
    target_levels = ['ELEVATION', 'EPICENTRAL_DISTANCE',
                     'GREATER_OF_TWO_HORIZONTALS', 'H1', 'H2', 'Z',
                     'HYPOCENTRAL_DISTANCE', 'LAT', 'LON', 'NAME', 'NETID', 'SOURCE',
                     'STATION', '', 'PGA', 'PGV', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)']

    # let's use sets to make sure all the columns are present in whatever order
    cmp1 = set(['ELEVATION', 'EPICENTRAL_DISTANCE',
                'GREATER_OF_TWO_HORIZONTALS', 'H1', 'H2',
                'HYPOCENTRAL_DISTANCE', 'LAT', 'LON',
                'NAME', 'NETID', 'SOURCE', 'STATION', 'Z'])
    cmp2 = set(['', 'PGA', 'PGV', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)'])
    header1 = set(df1.columns.levels[0])
    header2 = set(df1.columns.levels[1])
    assert header1 == cmp1
    assert header2 == cmp2
    # idx = 0
    # for s in df1.columns.levels:
    #     for col in s:
    #         try:
    #             assert col == target_levels[idx]
    #         except Exception as e:
    #             x = 1
    #         idx += 1

    # This was previously not being tested
    """imts = ['PGA', 'PGV', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)']
    imcs = ['GREATER_OF_TWO_HORIZONTALS', 'CHANNELS']
    homedir = os.path.dirname(os.path.abspath(__file__))

    datapath = os.path.join('data', 'testdata', 'knet')
    knet_dir = pkg_resources.resource_filename('gmprocess', datapath)
    # make dataframe
    knet_dataframe = directory_to_dataframe(knet_dir)

    # read and group streams
    streams = []
    for filepath in glob.glob(os.path.join(knet_dir, "*")):
        streams += read_data(filepath)
    grouped_streams = StreamCollection(streams)
    for idx, stream in enumerate(grouped_streams):
        stream = process_streams(stream)
        # set meta_data
        station = stream[0].stats['station']
        name_str = stream[0].stats['standard']['station_name']
        source = stream[0].stats.standard['source']
        network = stream[0].stats['network']
        latitude = stream[0].stats['coordinates']['latitude']
        longitude = stream[0].stats['coordinates']['longitude']
        # metadata from the dataframe
        knet_station = knet_dataframe.iloc[
            idx, knet_dataframe.columns.get_level_values(0) == 'STATION'][0]
        knet_name_str = knet_dataframe.iloc[
            idx, knet_dataframe.columns.get_level_values(0) == 'NAME'][0]
        knet_source = knet_dataframe.iloc[
            idx, knet_dataframe.columns.get_level_values(0) == 'SOURCE'][0]
        knet_network = knet_dataframe.iloc[
            idx, knet_dataframe.columns.get_level_values(0) == 'NETID'][0]
        knet_latitude = knet_dataframe.iloc[
            idx, knet_dataframe.columns.get_level_values(0) == 'LAT'][0]
        knet_longitude = knet_dataframe.iloc[
            idx, knet_dataframe.columns.get_level_values(0) == 'LON'][0]
        assert knet_station == station
        assert knet_name_str == name_str
        assert knet_source == source
        assert knet_network == network
        assert knet_latitude == latitude
        assert knet_longitude == longitude
        stream_summary = StationSummary.from_stream(stream, imcs, imts)
        pgms = stream_summary.pgms
        for imt in pgms:
            for imc in pgms[imt]:
                multi_idx = np.logical_and(
                    knet_dataframe.columns.get_level_values(1) == imt,
                    knet_dataframe.columns.get_level_values(0) == imc)
                dataframe_value = knet_dataframe.iloc[idx, multi_idx].to_list()[
                    0]
                streamsummary_value = pgms[imt][imc]
                assert dataframe_value == streamsummary_value

    datapath = os.path.join('data', 'testdata', 'cwb')
    cwb_dir = pkg_resources.resource_filename('gmprocess', datapath)
    # make dataframe
    cwb_dataframe = directory_to_dataframe(cwb_dir, lat=24.14, lon=121)

    # read and group streams
    streams = []
    for filepath in glob.glob(os.path.join(cwb_dir, "*")):
        streams += read_data(filepath)
    grouped_streams = StreamCollection(streams)
    for idx, stream in enumerate(grouped_streams):
        stream = process_streams(stream)
        # set meta_data
        station = stream[0].stats['station']
        name_str = stream[0].stats['standard']['station_name']
        source = stream[0].stats.standard['source']
        network = stream[0].stats['network']
        latitude = stream[0].stats['coordinates']['latitude']
        longitude = stream[0].stats['coordinates']['longitude']
        # metadata from the dataframe
        cwb_station = cwb_dataframe.iloc[
            idx, cwb_dataframe.columns.get_level_values(0) == 'STATION'][0]
        cwb_name_str = cwb_dataframe.iloc[
            idx, cwb_dataframe.columns.get_level_values(0) == 'NAME'][0]
        cwb_source = cwb_dataframe.iloc[
            idx, cwb_dataframe.columns.get_level_values(0) == 'SOURCE'][0]
        cwb_network = cwb_dataframe.iloc[
            idx, cwb_dataframe.columns.get_level_values(0) == 'NETID'][0]
        cwb_latitude = cwb_dataframe.iloc[
            idx, cwb_dataframe.columns.get_level_values(0) == 'LAT'][0]
        cwb_longitude = cwb_dataframe.iloc[
            idx, cwb_dataframe.columns.get_level_values(0) == 'LON'][0]
        assert cwb_station == station
        assert cwb_name_str == name_str
        assert cwb_source == source
        assert cwb_network == network
        assert cwb_latitude == latitude
        assert cwb_longitude == longitude
        stream_summary = StationSummary.from_stream(stream, imcs, imts)
        pgms = stream_summary.pgms
        for imt in pgms:
            for imc in pgms[imt]:
                multi_idx = np.logical_and(
                    cwb_dataframe.columns.get_level_values(1) == imt,
                    cwb_dataframe.columns.get_level_values(0) == imc)
                dataframe_value = cwb_dataframe.iloc[idx, multi_idx].to_list()[
                    0]
                streamsummary_value = pgms[imt][imc]
                assert dataframe_value == streamsummary_value"""


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_grouping()
    test()
    test_to_dataframe()
