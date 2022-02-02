#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Class for StationStream arrays.
"""

import copy
import fnmatch

from gmprocess.core.stationstream import StationStream

INDENT = 2


class StreamArray(object):
    def __init__(
        self,
        streams=None,
        config=None,
    ):
        """Initialize StreamCollection.

        Args:
            streams (list):
                List of StationStream objects.
            config (dict):
                Configuration options.
        """
        self.config = config
        if not isinstance(streams, list):
            raise TypeError("streams must be a list of StationStream objects.")
        newstreams = []
        for st in streams:
            if not isinstance(st, StationStream):
                raise TypeError("streams must be a list of StationStream objects.")
            else:
                st.id = ".".join(
                    [
                        st[0].stats.network,
                        st[0].stats.station,
                        st[0].stats.location,
                        st[0].stats.channel,
                    ],
                )
                st.use_array = True
                newstreams.append(st)
        self.streams = newstreams

    def describe(self):
        """More verbose description of StreamArray."""
        summary = ""
        summary += str(len(self.streams)) + " StationStreams(s) in StreamArray:\n"
        for stream in self:
            summary += stream.__str__(indent=INDENT) + "\n"
        print(summary)

    def __len__(self):
        """Number of constituent StationStreams."""
        return len(self.streams)

    def __nonzero__(self):
        return bool(len(self.traces))

    def __add__(self, other):
        if not isinstance(other, StreamArray):
            raise TypeError
        streams = self.streams + other.streams
        return self.__class__(streams)

    def __iter__(self):
        """Iterator for GMCollection over constituent StationStreams."""
        return list(self.streams).__iter__()

    def __setitem__(self, index, stream):
        self.streams.__setitem__(index, stream)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self.__class__(stream=self.streams.__getitem__(index))
        else:
            return self.streams.__getitem__(index)

    def __delitem__(self, index):
        return self.streams.__delitem__(index)

    def __getslice__(self, i, j, k=1):
        return self.__class__(streams=self.streams[max(0, i) : max(0, j) : k])

    def append(self, stream):
        """Append a single StationStream object.

        Args:
            stream:
                A StationStream object.
        """
        if isinstance(stream, StationStream):
            streams = self.streams + [stream]
            return self.__class__(streams)
        else:
            raise TypeError("Append only uspports adding a single StationStream.")

    def pop(self, index=(-1)):
        """Remove and return item at index (default last)."""
        return self.streams.pop(index)

    def copy(self):
        """Copy method."""
        return copy.deepcopy(self)

    def select(self, network=None, station=None, instrument=None):
        """Select Streams.

        Return a new StreamCollection with only those StationStreams that
        match network, station, and/or instrument selection criteria.

        Based on obspy's `select` method for traces.

        Args:
            network (str):
                Network code.
            station (str):
                Station code.
            instrument (str):
                Instrument code; i.e., the first two characters of the
                channel.
        """
        sel = []
        for st in self:
            inst = st.get_inst()
            net_sta = st.get_net_sta()
            net = net_sta.split(".")[0]
            sta = net_sta.split(".")[1]
            if network is not None:
                if not fnmatch.fnmatch(net.upper(), network.upper()):
                    continue
            if station is not None:
                if not fnmatch.fnmatch(sta.upper(), station.upper()):
                    continue
            if instrument is not None:
                if not fnmatch.fnmatch(inst.upper(), instrument.upper()):
                    continue
            sel.append(st)
        return self.__class__(sel)

    @property
    def n_passed(self):
        n_passed = 0
        for stream in self:
            if stream.passed:
                n_passed += 1
        return n_passed

    @property
    def n_failed(self):
        n = len(self.streams)
        return n - self.n_passed
