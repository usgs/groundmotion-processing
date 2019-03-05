"""
Module for StreamCollection class.

This class functions as a list of StationStream objects, and enforces
various rules, such as all traces within a stream are from the same station.
"""

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
        self.__group_by_net_sta()

    def __group_by_net_sta(self):
        trace_list = []
        for stream in self.streams:
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
            for idx2, trace2 in enumerate(trace_list):
                if idx1 != idx2 and idx1 not in all_matches:
                    if (
                        network == trace2.stats['network'] and
                        station == trace2.stats['station']
                    ):
                        matches.append(idx2)
            if len(matches) > 1:
                match_list.append(matches)
                all_matches.extend(matches)
            else:
                if matches[0] not in all_matches:
                    match_list.append(matches)
                    all_matches.extend(matches)

        self.streams = match_list
