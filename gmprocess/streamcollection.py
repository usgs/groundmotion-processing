"""
Module for StreamCollection class.

This class functions as a list of StationStream objects, and enforces
various rules, such as all traces within a stream are from the same station.
"""

import numpy as np

from gmprocess.stationstream import StationStream


class StreamCollection(object):
    """
    A collection/list of StationStream objects.

    This is a list of StationStream objectss, where the constituent
    StationTraces are grouped such that:

        - All traces are from the same network/station.
        - Sample rates must match.
        - Units much match.
        - All start/end times must match; if they do not match and
          other checks pass then the traces are resampled to have
          matching start/end times.

    """

    def __init__(self, streams=None):
        """
        Args:
            streams (list): List of StationStream objects.
        """

        # Some initial checks of input streams
        if not isinstance(streams, list):
            raise TypeError(
                'streams must be a list of StationStream objects.')
        for s in streams:
            if not isinstance(s, StationStream):
                raise TypeError(
                    'streams must be a list of StationStream objects.')

        self.streams = streams
        self.__group_by_net_sta_inst()

        # Check that sample rate is consistent within each StationStream
        for stream in self:
            self.__check_sample_rate(stream)

        # Snap start/end times to match if they do not match. I think this
        # should only come up for hand digitized records of analog
        # instruments.
        self.__snap_start_end_times()

    def __len__(self):
        """
        Length of StreamCollection is the number of constituent StationStreams.
        """
        return len(self.streams)

    def __nonzero__(self):
        """
        Nonzero if there are no StationStreams.
        """
        return bool(len(self.traces))

    def __add__(self, other):
        """
        Add two streams together means appending to list of streams.
        """
        if not isinstance(other, StreamCollection):
            raise TypeError
        streams = self.streams + other.streams
        return self.__class__(streams)

    def __iter__(self):
        """
        Iterator for StreamCollection iterates over constituent StationStreams.
        """
        return list(self.streams).__iter__()

    def __setitem__(self, index, stream):
        """
        __setitem__ method.
        """
        self.streams.__setitem__(index, stream)

    def __getitem__(self, index):
        """
        __getitem__ method.
        """
        if isinstance(index, slice):
            return self.__class__(stream=self.streams.__getitem__(index))
        else:
            return self.streams.__getitem__(index)

    def __delitem__(self, index):
        """
        __delitem__ method.
        """
        return self.streams.__delitem__(index)

    def __getslice__(self, i, j, k=1):
        """
        Getslice method.
        """
        return self.__class__(streams=self.streams[max(0, i):max(0, j):k])

    def pop(self, index=(-1)):
        """
        Remove and return the StationStream object specified by index from
        the StreamCollection.
        """
        return self.streams.pop(index)

    def __group_by_net_sta_inst(self):
        trace_list = []
        for stream in self:
            for trace in stream:
                trace_list += [trace]

        # Create a list of traces with matching net, sta.
        all_matches = []
        match_list = []
        for idx1, trace1 in enumerate(trace_list):
            if idx1 in all_matches:
                continue
            matches = [idx1]
            network = trace1.stats['network']
            station = trace1.stats['station']
            # For instrument, use first two characters of the channel
            inst = trace1.stats['channel'][0:2]
            for idx2, trace2 in enumerate(trace_list):
                if idx1 != idx2 and idx1 not in all_matches:
                    if (
                        network == trace2.stats['network'] and
                        station == trace2.stats['station'] and
                        inst == trace2.stats['channel'][0:2]
                    ):
                        matches.append(idx2)
            if len(matches) > 1:
                match_list.append(matches)
                all_matches.extend(matches)
            else:
                if matches[0] not in all_matches:
                    match_list.append(matches)
                    all_matches.extend(matches)

        grouped_streams = []
        for groups in match_list:
            grouped_trace_list = []
            for i in groups:
                grouped_trace_list.append(
                    trace_list[i]
                )
            grouped_streams.append(
                StationStream(grouped_trace_list)
            )

        self.streams = grouped_streams

    def __snap_start_end_times(self):
        # First deal with the start times
        for stream in self:
            start_times = []
            for tr in stream:
                start_times.append(tr.stats.starttime)

#        if not (start_times[0] == start_times):
#
#        print('')

    @staticmethod
    def __check_sample_rate(stream):
        first_sample_rate = stream[0].stats['sampling_rate']
        for tr in stream:
            if first_sample_rate != tr.stats['sampling_rate']:
                raise ValueError('All stream sample rates much be the same.')
