#!/usr/bin/env python

# stdlib imports
import glob
import os.path
from io import StringIO
import logging

# third party imports
import numpy as np
from gmprocess.io.geonet.core import read_geonet
from gmprocess.io.knet.core import read_knet
from gmprocess.io.read import read_data
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.process import process_config
from gmprocess.stream import (group_channels,
                              streams_to_dataframe,
                              directory_to_dataframe)


def test():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?

    # Test for channel grouping with three unique channels
    streams = []
    datadir = os.path.join(homedir, '..', 'data', 'knet')
    for ext in ['.EW', '.NS', '.UD']:
        filename = 'AOM0031801241951' + ext
        datafile = os.path.join(homedir, '..', 'data', 'knet', filename)
        streams += [read_knet(datafile)]
    grouped_streams = group_channels(streams)
    assert len(grouped_streams) == 1
    assert grouped_streams[0].count() == 3

    # Test for channel grouping with three more duplicate channels
    for ext in ['.EW', '.NS', '.UD']:
        filename = 'AOM0031801241951' + ext
        datafile = os.path.join(homedir, '..', 'data', 'knet', filename)
        streams += [read_knet(datafile)]
    grouped_streams = group_channels(streams)
    assert len(grouped_streams) == 1
    assert grouped_streams[0].count() == 3

    # Test for channel grouping with more file types
    filename = '20161113_110313_THZ_20.V2A'
    datafile = os.path.join(homedir, '..', 'data', 'geonet', filename)
    streams += [read_geonet(datafile)]
    grouped_streams = group_channels(streams)
    assert len(grouped_streams) == 2
    assert grouped_streams[0].count() == 3
    assert grouped_streams[1].count() == 3

    # Test for warning for one channel streams
    filename = 'AOM0071801241951.UD'
    datafile = os.path.join(homedir, '..', 'data', 'knet', filename)
    streams += [read_knet(datafile)]

    # * This is my attempt to do this after changing from
    #   warnings.warn to logging.warning but it doesn't seem
    #   to work.
#    logstream = StringIO()
#    handler = logging.StreamHandler(logstream)
#    log = logging.getLogger()
#    log.setLevel(logging.INFO)
#    for handler in log.handlers:
#        log.removeHandler(handler)
#    log.addHandler(handler)
#    handler.flush()
    grouped_streams = group_channels(streams)
#    assert "One channel stream:" in logstream.getvalue()

    assert len(grouped_streams) == 3
    assert grouped_streams[0].count() == 3
    assert grouped_streams[1].count() == 3
    assert grouped_streams[2].count() == 1


def test_grouping():
    homedir = os.path.dirname(os.path.abspath(__file__))

    # cwb
    cwb_files = os.path.join(homedir, '..', 'data', 'cwb', '*')
    cwb_streams = []
    for filename in glob.glob(cwb_files):
        cwb_streams += [read_data(filename)]
    cwb_streams = group_channels(cwb_streams)
    assert len(cwb_streams) == 5
    for stream in cwb_streams:
        assert len(stream) == 3

    # dmg
    dmg_files = os.path.join(homedir, '..', 'data', 'dmg', '*.V2')
    dmg_streams = []
    for filename in glob.glob(dmg_files):
        if (not os.path.basename(filename).startswith('Bad') and
                not os.path.basename(filename).startswith('CE58667')):
            dmg_streams += [read_data(filename)]
    dmg_streams = group_channels(dmg_streams)
    assert len(dmg_streams) == 2
    for stream in dmg_streams:
        assert len(stream) == 3

    # geonet
    geonet_files = os.path.join(homedir, '..', 'data', 'geonet', '*')
    geonet_streams = []
    for filename in glob.glob(geonet_files):
        geonet_streams += [read_data(filename)]
    geonet_streams = group_channels(geonet_streams)
    assert len(geonet_streams) == 7
    for stream in geonet_streams:
        assert len(stream) == 3
        assert len(stream.select(station=stream[0].stats.station)) == 3
        level = stream[0].stats.standard.process_level
        for trace in stream:
            assert trace.stats.standard.process_level == level

    # kiknet
    kiknet_files = os.path.join(homedir, '..', 'data', 'kiknet', '*')
    kiknet_streams = []
    for filename in glob.glob(kiknet_files):
        kiknet_streams += [read_data(filename)]
    kiknet_streams = group_channels(kiknet_streams)
    assert len(kiknet_streams) == 1
    for stream in kiknet_streams:
        assert len(stream) == 3
        assert len(stream.select(station=stream[0].stats.station)) == 3

    # knet
    knet_files = os.path.join(homedir, '..', 'data', 'knet', '*')
    knet_streams = []
    for filename in glob.glob(knet_files):
        knet_streams += [read_data(filename)]
    knet_streams = group_channels(knet_streams)
    assert len(knet_streams) == 9
    for stream in knet_streams:
        assert len(stream) == 3
        assert len(stream.select(station=stream[0].stats.station)) == 3
        pl = stream[0].stats.standard.process_level
        for trace in stream:
            assert trace.stats.standard.process_level == pl

    # obspy
    obspy_files = os.path.join(homedir, '..', 'data', 'obspy', '*')
    obspy_streams = []
    for filename in glob.glob(obspy_files):
        if not filename.endswith('.json'):
            obspy_streams += [read_data(filename)]
    obspy_streams = group_channels(obspy_streams)
    assert len(obspy_streams) == 1
    for stream in obspy_streams:
        assert len(stream) == 3
        assert len(stream.select(station=stream[0].stats.station)) == 3

    # smc
    smc_files = os.path.join(homedir, '..', 'data', 'smc', '*')
    smc_streams = []
    for filename in glob.glob(smc_files):
        if not filename.endswith('.json'):
            smc_streams += [read_data(filename, any_structure=True)]
    smc_streams = group_channels(smc_streams)
    assert len(smc_streams) == 6
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
    usc_files = os.path.join(homedir, '..', 'data', 'usc', '*')
    usc_streams = []
    for filename in glob.glob(usc_files):
        if not filename.endswith('.json'):
            if os.path.basename(filename) != '017m30bt.s0a':
                usc_streams += [read_data(filename)]
    usc_streams = group_channels(usc_streams)
    assert len(usc_streams) == 3
    for stream in usc_streams:
        if stream[0].stats.station == '57':
            assert len(stream) == 1
        else:
            assert len(stream) == 3


def test_directory_to_dataframe():
    imts = ['PGA', 'PGV', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)']
    imcs = ['GREATER_OF_TWO_HORIZONTALS', 'CHANNELS']
    homedir = os.path.dirname(os.path.abspath(__file__))

    knet_dir = os.path.join(homedir, '..', 'data', 'knet')
    # make dataframe
    knet_dataframe = directory_to_dataframe(knet_dir)

    # read and group streams
    streams = []
    for filepath in glob.glob(os.path.join(knet_dir, "*")):
        streams += [read_data(filepath)]
    grouped_streams = group_channels(streams)
    for idx, stream in enumerate(grouped_streams):
        stream = process_config(stream)
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

    geonet_dir = os.path.join(homedir, '..', 'data', 'geonet')
    # make dataframe
    geonet_dataframe = directory_to_dataframe(geonet_dir)

    # read and group streams
    streams = []
    for filepath in glob.glob(os.path.join(geonet_dir, "*")):
        streams += [read_data(filepath)]
    grouped_streams = group_channels(streams)
    for idx, stream in enumerate(grouped_streams):
        stream = process_config(stream)
        # set meta_data
        station = stream[0].stats['station']
        name_str = stream[0].stats['standard']['station_name']
        source = stream[0].stats.standard['source']
        network = stream[0].stats['network']
        latitude = stream[0].stats['coordinates']['latitude']
        longitude = stream[0].stats['coordinates']['longitude']
        # metadata from the dataframe
        geonet_station = geonet_dataframe.iloc[
            idx, geonet_dataframe.columns.get_level_values(0) == 'STATION'][0]
        geonet_name_str = geonet_dataframe.iloc[
            idx, geonet_dataframe.columns.get_level_values(0) == 'NAME'][0]
        geonet_source = geonet_dataframe.iloc[
            idx, geonet_dataframe.columns.get_level_values(0) == 'SOURCE'][0]
        geonet_network = geonet_dataframe.iloc[
            idx, geonet_dataframe.columns.get_level_values(0) == 'NETID'][0]
        geonet_latitude = geonet_dataframe.iloc[
            idx, geonet_dataframe.columns.get_level_values(0) == 'LAT'][0]
        geonet_longitude = geonet_dataframe.iloc[
            idx, geonet_dataframe.columns.get_level_values(0) == 'LON'][0]
        assert geonet_station == station
        assert geonet_name_str == name_str
        assert geonet_source == source
        assert geonet_network == network
        assert geonet_latitude == latitude
        assert geonet_longitude == longitude
        stream_summary = StationSummary.from_stream(stream, imcs, imts)
        pgms = stream_summary.pgms
        for imt in pgms:
            for imc in pgms[imt]:
                multi_idx = np.logical_and(
                    geonet_dataframe.columns.get_level_values(1) == imt,
                    geonet_dataframe.columns.get_level_values(0) == imc)
                dataframe_value = geonet_dataframe.iloc[idx, multi_idx].to_list()[
                    0]
                streamsummary_value = pgms[imt][imc]
                assert dataframe_value == streamsummary_value


if __name__ == '__main__':
    test_grouping()
    test()
    test_directory_to_dataframe()
