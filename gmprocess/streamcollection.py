"""
Module for StreamCollection class.

This class functions as a list of StationStream objects, and enforces
various rules, such as all traces within a stream are from the same station.
"""

import copy

import numpy as np
from obspy.geodetics import gps2dist_azimuth
from obspy.core.event import Origin
import pandas as pd

from gmprocess.io.read_directory import directory_to_streams
from gmprocess.stationstream import StationStream
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.exception import GMProcessException

INDENT = 2

DEFAULT_IMTS = ['PGA', 'PGV', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)']
DEFAULT_IMCS = ['GREATER_OF_TWO_HORIZONTALS', 'CHANNELS']


class StreamCollection(object):
    """
    A collection/list of StationStream objects.

    This is a list of StationStream objectss, where the constituent
    StationTraces are grouped such that:

        - All traces are from the same network/station.
        - Sample rates must match.
        - Units much match.

    TODO:
        - Check for and handle misaligned start times and end times.
        - Check units

    """

    def __init__(self, streams=None, drop_non_free=True):
        """
        Args:
            streams (list):
                List of StationStream objects.
            drop_non_free (bool):
                If True, drop non-free-field Streams from the collection.
        """

        # Some initial checks of input streams
        if not isinstance(streams, list):
            raise TypeError(
                'streams must be a list of StationStream objects.')
        newstreams = []
        for s in streams:
            if not isinstance(s, StationStream):
                raise TypeError(
                    'streams must be a list of StationStream objects.')
            if drop_non_free:
                if s[0].free_field:
                    newstreams.append(s)
            else:
                newstreams.append(s)

        self.streams = newstreams
        self.__group_by_net_sta_inst()

        self.validate()

    def validate(self):
        """Some validation checks across streams.

        """
        # If tag exists, it should be consistent across StationStreams
        all_labels = []
        for stream in self:
            if hasattr(stream, 'tag'):
                station, label = stream.tag.split('_')
                all_labels.append(label)
            else:
                all_labels.append("")
        if len(set(all_labels)) > 1:
            raise GMProcessException(
                'Only one label allowed within a StreamCollection.')

    @classmethod
    def from_directory(cls, directory):
        """
        Create a StreamCollection instance from a directory of data.

        Args:
            directory (str):
                Directory of ground motion files (streams) to be read.

        Returns:
            StreamCollection instance.
        """
        streams, missed_files, errors = directory_to_streams(directory)

        # Might eventually want to include some of the missed files and
        # error info but don't have a sensible place to put it currently.

        return cls(streams)

    def to_dataframe(self, origin_dict, imcs=None, imts=None):
        """Get a summary dataframe of streams.

        Note: The PGM columns underneath each channel will be variable
        depending on the units of the Stream being passed in (velocity
        sensors can only generate PGV) and on the imtlist passed in by
        user. Spectral acceleration columns will be formatted as SA(0.3)
        for 0.3 second spectral acceleration, for example.

        Args:
            directory (str):
                Directory of ground motion files (streams).
            origin_dict (dict):
                Dictionary with the following keys:
                   - id
                   - magnitude
                   - time (UTCDateTime object)
                   - lon
                   - lat
                   - depth
            imcs (list):
                Strings designating desired components to create in table.
            imts (list):
                Strings designating desired PGMs to create in table.

        Returns:
            DataFrame: Pandas dataframe containing columns:
                - STATION Station code.
                - NAME Text description of station.
                - LOCATION Two character location code.
                - SOURCE Long form string containing source network.
                - NETWORK Short network code.
                - LAT Station latitude
                - LON Station longitude
                - DISTANCE Epicentral distance (km) (if epicentral
                  lat/lon provided)
                - HN1 East-west channel (or H1) (multi-index with pgm columns):
                    - PGA Peak ground acceleration (%g).
                    - PGV Peak ground velocity (cm/s).
                    - SA(0.3) Pseudo-spectral acceleration at 0.3 seconds (%g).
                    - SA(1.0) Pseudo-spectral acceleration at 1.0 seconds (%g).
                    - SA(3.0) Pseudo-spectral acceleration at 3.0 seconds (%g).
                - HN2 North-south channel (or H2) (multi-index with pgm
                  columns):
                    - PGA Peak ground acceleration (%g).
                    - PGV Peak ground velocity (cm/s).
                    - SA(0.3) Pseudo-spectral acceleration at 0.3 seconds (%g).
                    - SA(1.0) Pseudo-spectral acceleration at 1.0 seconds (%g).
                    - SA(3.0) Pseudo-spectral acceleration at 3.0 seconds (%g).
                - HNZ Vertical channel (or HZ) (multi-index with pgm columns):
                    - PGA Peak ground acceleration (%g).
                    - PGV Peak ground velocity (cm/s).
                    - SA(0.3) Pseudo-spectral acceleration at 0.3 seconds (%g).
                    - SA(1.0) Pseudo-spectral acceleration at 1.0 seconds (%g).
                    - SA(3.0) Pseudo-spectral acceleration at 3.0 seconds (%g).
                - GREATER_OF_TWO_HORIZONTALS (multi-index with pgm columns):
                    - PGA Peak ground acceleration (%g).
                    - PGV Peak ground velocity (cm/s).
                    - SA(0.3) Pseudo-spectral acceleration at 0.3 seconds (%g).
                    - SA(1.0) Pseudo-spectral acceleration at 1.0 seconds (%g).
                    - SA(3.0) Pseudo-spectral acceleration at 3.0 seconds (%g).
        """
        streams = self.streams
        num_streams = len(streams)

        if imcs is None:
            station_summary_imcs = DEFAULT_IMCS
        else:
            station_summary_imcs = imcs
        if imts is None:
            station_summary_imts = DEFAULT_IMTS
        else:
            station_summary_imts = imts

        columns = ['STATION', 'NAME', 'SOURCE',
                   'NETID', 'LAT', 'LON', 'DISTANCE']
        meta_data = np.empty((num_streams, len(columns)), dtype=list)

        station_pgms = []
        imcs = []
        imts = []
        for idx, stream in enumerate(streams):
            # set meta_data
            meta_data[idx][0] = stream[0].stats['station']
            name_str = stream[0].stats['standard']['station_name']
            meta_data[idx][1] = name_str
            source = stream[0].stats.standard['source']
            meta_data[idx][2] = source
            meta_data[idx][3] = stream[0].stats['network']
            latitude = stream[0].stats['coordinates']['latitude']
            meta_data[idx][4] = latitude
            longitude = stream[0].stats['coordinates']['longitude']
            meta_data[idx][5] = longitude

            dist, _, _ = gps2dist_azimuth(
                origin_dict['lat'], origin_dict['lon'], latitude, longitude)
            meta_data[idx][6] = dist / 1000

            origin_obj = Origin(latitude=origin_dict['lat'],
                                longitude=origin_dict['lon'])

            stream_summary = StationSummary.from_stream(
                stream, station_summary_imcs, station_summary_imts, origin_obj)
            pgms = stream_summary.pgms
            station_pgms += [pgms]
            imcs += stream_summary.components
            imts += stream_summary.imts

        meta_columns = pd.MultiIndex.from_product([columns, ['']])
        meta_dataframe = pd.DataFrame(meta_data, columns=meta_columns)
        imcs = np.unique(imcs)
        imts = np.unique(imts)
        pgm_columns = pd.MultiIndex.from_product([imcs, imts])
        pgm_data = np.zeros((num_streams, len(imts) * len(imcs)))
        for idx, station in enumerate(station_pgms):
            subindex = 0
            for imc in imcs:
                for imt in imts:
                    pgm_data[idx][subindex] = station[imt][imc]
                    subindex += 1
        pgm_dataframe = pd.DataFrame(pgm_data, columns=pgm_columns)

        dataframe = pd.concat([meta_dataframe, pgm_dataframe], axis=1)

        return dataframe

    def __str__(self):
        """
        String summary of the StreamCollection.
        """
        summary = ''
        n = len(self.streams)
        summary += '%s StationStreams(s) in StreamCollection:\n' % n
        n_passed = 0
        for stream in self:
            if stream.passed:
                n_passed += 1
        summary += '    %s StationStreams(s) passed checks.\n' % n_passed
        n_failed = n - n_passed
        summary += '    %s StationStreams(s) failed checks.\n' % n_failed
        return summary

    def describe(self):
        """
        More verbose description of StreamCollection.
        """
        summary = ''
        summary += str(len(self.streams)) + \
            ' StationStreams(s) in StreamCollection:\n'
        for stream in self:
            summary += stream.__str__(indent=INDENT) + '\n'
        print(summary)

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

    def append(self, stream):
        """
        Append a single StationStream object.

        Args:
            stream:
                A StationStream object.
        """
        if isinstance(stream, StationStream):
            streams = self.streams + [stream]
            return self.__class__(streams)
        else:
            raise TypeError(
                'Append only uspports adding a single StationStream.')

    def pop(self, index=(-1)):
        """
        Remove and return the StationStream object specified by index from
        the StreamCollection.
        """
        return self.streams.pop(index)

    def copy(self):
        """
        Copy method.
        """
        return copy.deepcopy(self)

    def __group_by_net_sta_inst(self, drop_error_streams=True):
        trace_list = []

        # Need to make sure that tag will be preserved; tag only really should
        # be created once a StreamCollection has been written to an ASDF file
        # and then read back in.
        for stream in self:
            # Tag is a StationStream attribute; If it does not exist, make it
            # an empty string
            if hasattr(stream, 'tag'):
                tag = stream.tag
            else:
                tag = ""
            # Since we have to deconstruct the stream groupings each time, we
            # need to stick the tag into the trace stats dictionary temporarily
            for trace in stream:
                tr = trace
                tr.stats.tag = tag
                trace_list += [tr]

        # Create a list of traces with matching net, sta.
        all_matches = []
        match_list = []
        for idx1, trace1 in enumerate(trace_list):
            if idx1 in all_matches:
                continue
            matches = [idx1]
            network = trace1.stats['network']
            station = trace1.stats['station']
            free_field = trace1.free_field
            # For instrument, use first two characters of the channel
            inst = trace1.stats['channel'][0:2]
            for idx2, trace2 in enumerate(trace_list):
                if idx1 != idx2 and idx1 not in all_matches:
                    if (
                        network == trace2.stats['network']
                        and station == trace2.stats['station']
                        and inst == trace2.stats['channel'][0:2]
                        and free_field == trace2.free_field
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
            st = StationStream(grouped_trace_list)
            if len(st):
                # Put tag back as a stream attribute, assuming that the
                # tag has stayed the same through the grouping process
                if st[0].stats.tag:
                    st.tag = st[0].stats.tag
                grouped_streams.append(st)

        self.streams = grouped_streams
