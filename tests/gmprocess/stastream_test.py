#!/usr/bin/env python

import numpy as np
from obspy.core.utcdatetime import UTCDateTime
from obspy.core.trace import Trace

from gmprocess.stationstream import StationStream

from invutils import get_inventory


def test_stream():
    inventory = get_inventory()
    channels = ['HN1', 'HN2', 'HNZ']
    data = np.random.rand(1000)
    traces = []
    network = inventory.networks[0]
    station = network.stations[0]
    chlist = station.channels
    channelcodes = [ch.code for ch in chlist]
    for channel in channels:
        chidx = channelcodes.index(channel)
        channeldata = chlist[chidx]
        header = {'sampling_rate': channeldata.sample_rate,
                  'npts': len(data),
                  'network': network.code,
                  'location': channeldata.location_code,
                  'station': station.code,
                  'channel': channel,
                  'starttime': UTCDateTime(2010, 1, 1, 0, 0, 0)}
        trace = Trace(data=data, header=header)
        traces.append(trace)
    invstream = StationStream(traces=traces, inventory=inventory)
    inventory2 = invstream.getInventory()
    inv2_channel1 = inventory2.networks[0].stations[0].channels[0]
    inv_channel1 = inventory2.networks[0].stations[0].channels[0]
    assert inv_channel1.code == inv2_channel1.code


if __name__ == '__main__':
    test_stream()
