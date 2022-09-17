#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from obspy.core.utcdatetime import UTCDateTime
from obspy.core.trace import Trace

from gmprocess.core.stationstream import StationStream
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.constants import TEST_DATA_DIR

from invutils import get_inventory


def test_stream():
    inventory = get_inventory()
    channels = ["HN1", "HN2", "HNZ"]
    data = np.random.rand(1000)
    traces = []
    network = inventory.networks[0]
    station = network.stations[0]
    chlist = station.channels
    channelcodes = [ch.code for ch in chlist]
    for channel in channels:
        chidx = channelcodes.index(channel)
        channeldata = chlist[chidx]
        header = {
            "sampling_rate": channeldata.sample_rate,
            "npts": len(data),
            "network": network.code,
            "location": channeldata.location_code,
            "station": station.code,
            "channel": channel,
            "starttime": UTCDateTime(2010, 1, 1, 0, 0, 0),
        }
        trace = Trace(data=data, header=header)
        traces.append(trace)
    invstream = StationStream(traces=traces, inventory=inventory)
    inventory2 = invstream.getInventory()
    inv2_channel1 = inventory2.networks[0].stations[0].channels[0]
    inv_channel1 = inventory2.networks[0].stations[0].channels[0]
    assert inv_channel1.code == inv2_channel1.code

    # test the streamparam functionality
    statsdict = {"name": "Fred", "age": 34}
    invstream.setStreamParam("stats", statsdict)
    stream_params = invstream.getStreamParamKeys()
    stream_params.sort()
    assert stream_params == ["any_trace_failures", "stats"]
    cmpdict = invstream.getStreamParam("stats")
    assert statsdict == cmpdict


def test_uneven_stream():
    inventory = get_inventory()
    channels = ["HN1", "HN2", "HNZ"]
    data1 = np.random.rand(1000)
    data2 = np.random.rand(1001)
    data3 = np.random.rand(1002)
    data = [data1, data2, data3]
    traces = []
    network = inventory.networks[0]
    station = network.stations[0]
    chlist = station.channels
    channelcodes = [ch.code for ch in chlist]
    for datat, channel in zip(data, channels):
        chidx = channelcodes.index(channel)
        channeldata = chlist[chidx]
        header = {
            "sampling_rate": channeldata.sample_rate,
            "npts": len(datat),
            "network": network.code,
            "location": channeldata.location_code,
            "station": station.code,
            "channel": channel,
            "starttime": UTCDateTime(2010, 1, 1, 0, 0, 0),
        }
        trace = Trace(data=datat, header=header)
        traces.append(trace)
    invstream = StationStream(traces=traces, inventory=inventory)
    x = 1


def test_num_horizontals():
    sc = StreamCollection.from_directory(
        TEST_DATA_DIR / "fdsn" / "uw61251926" / "strong_motion"
    )
    st = sc.select(station="SP2")[0]
    assert st.num_horizontal == 2

    for tr in st:
        tr.stats.channel = "ENZ"
    assert st.num_horizontal == 0

    for tr in st:
        tr.stats.channel = "EN1"
    assert st.num_horizontal == 3


if __name__ == "__main__":
    test_uneven_stream()
    test_stream()
