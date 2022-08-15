#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for StreamCollection class.

This class functions as a list of StationStream objects, and enforces
various rules, such as all traces within a stream are from the same station.
"""

import re
import logging

from obspy import UTCDateTime
from obspy.core.event import Origin
from obspy.geodetics import gps2dist_azimuth
import pandas as pd
import numpy as np

from gmprocess.core.streamarray import StreamArray
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import REV_PROCESS_LEVELS
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.io.read_directory import directory_to_streams
from gmprocess.utils.config import get_config


INDENT = 2

DEFAULT_IMTS = ["PGA", "PGV", "SA(0.3)", "SA(1.0)", "SA(3.0)"]
DEFAULT_IMCS = ["GREATER_OF_TWO_HORIZONTALS", "CHANNELS"]

NETWORKS_USING_LOCATION = ["RE"]


class StreamCollection(StreamArray):
    """A collection/list of StationStream objects.

    This is a list of StationStream objects, where the constituent
    StationTraces are grouped such that:

        - All traces are from the same network/station/instrument.
        - Sample rates must match.
        - Units much match.

    TODO:
        - Check for and handle misaligned start times and end times.
        - Check units
    """

    def __init__(
        self,
        streams=None,
        drop_non_free=True,
        handle_duplicates=True,
        max_dist_tolerance=None,
        preference_order=None,
        process_level_preference=None,
        format_preference=None,
        config=None,
    ):
        """Initialize StreamCollection.

        Args:
            streams (list):
                List of StationStream objects.
            drop_non_free (bool):
                If True, drop non-free-field Streams from the collection.
            hande_duplicates (bool):
                If True, remove duplicate data from the collection.
            max_dist_tolerance (float):
                Maximum distance tolerance for determining whether two streams
                are at the same location (in meters).
            preference_order (list):
                A list containing 'process_level', 'source_format',
                'starttime', 'npts', 'sampling_rate', 'location_code' in the
                desired order for choosing the preferred trace.
            process_level_preference (list):
                A list containing 'V0', 'V1', 'V2', with the order determining
                which process level is the most preferred (most preferred goes
                first in the list).
            format_preference (list):
                A list continaing strings of the file source formats (found
                in gmprocess.io). Does not need to list all of the formats.
                Example: ['cosmos', 'dmg'] indicates that cosmos files are
                preferred over dmg files.
            config (dict):
                Configuration options.
        """
        self.config = config
        # Some initial checks of input streams
        if not isinstance(streams, list):
            raise TypeError("streams must be a list of StationStream objects.")
        newstreams = []
        for st in streams:
            if not isinstance(st, StationStream):
                raise TypeError("streams must be a list of StationStream objects.")

            logging.debug(st.get_id())
            st.id = st.get_id()
            st.use_array = False

            if drop_non_free:
                if st[0].free_field:
                    newstreams.append(st)
                else:
                    logging.debug(
                        f"Omitting station trace {st[0].id} from stream collection "
                        "because it is not free field."
                    )
            else:
                newstreams.append(st)

        self.streams = newstreams
        if handle_duplicates:
            if len(self.streams):
                self.__handle_duplicates(
                    max_dist_tolerance,
                    preference_order,
                    process_level_preference,
                    format_preference,
                )
        self.__group_by_net_sta_inst()
        self.validate()

    def validate(self):
        """Some validation checks across streams."""
        # If tag exists, it should be consistent across StationStreams
        all_labels = []
        for stream in self:
            if hasattr(stream, "tag"):
                parts = stream.tag.split("_")
                if len(parts) > 2:
                    label = parts[-1]
                    eventid = "_".join(parts[0:-1])
                else:
                    eventid, label = stream.tag.split("_")
                all_labels.append(label)
            else:
                all_labels.append("")
        if len(set(all_labels)) > 1:
            raise ValueError("Only one label allowed within a StreamCollection.")

    def select_colocated(
        self, preference=["HN?", "BN?", "HH?", "BH?"], large_dist=None, origin=None
    ):
        """Detect colocated instruments, return preferred instrument type.

        This uses the list of the first two channel characters, given as
        'preference' in the 'colocated' section of the config. The algorithm
        is:

            1) Generate list of StationStreams that have the same station code.
            2) For each colocated group, loop over the list of preferred
               instrument codes, select the first one that is encountered by
               labeling all others a failed.

                * If the preferred instrument type matches more than one
                  StationStream, pick the first (hopefully this never happens).
                * If no StationStream matches any of the codes in the preferred
                  list then label all as failed.

        Args:
            preference (list):
                List of strings indicating preferred instrument types.
            large_dist (dict):
                A dictionary with keys "preference", "mag", and "dist";
                "preference" is the same as the "preference" argument to this
                function, but will replace it when the distance is exceeded
                for a given magnitude. The distance threshold is computed as:

                    ```
                    dist_thresh = dist[0]
                    for m, d in zip(mag, dist):
                        if eqmag > m:
                            dist_thresh = d
                    ```

            origin (Origin):
                Origin object.
        """
        # Do we have different large distnce preference?
        if large_dist is not None and large_dist["enabled"]:
            dist_thresh = large_dist["dist"][0]
            for m, d in zip(large_dist["mag"], large_dist["dist"]):
                if origin.magnitude > m:
                    dist_thresh = d

        # Create a list of streams with matching id (combo of net and station).
        all_matches = []
        match_list = []
        for idx1, stream1 in enumerate(self):
            cond1 = idx1 in all_matches
            cond2 = not stream1.passed
            if cond1 or cond2:
                continue
            matches = [idx1]
            net_sta = stream1.get_net_sta()
            for idx2, stream2 in enumerate(self):
                cond1 = idx1 != idx2
                cond2 = idx1 not in all_matches
                cond3 = net_sta == stream2.get_net_sta()
                cond4 = stream2.passed
                if cond1 and cond2 and cond3 and cond4:
                    matches.append(idx2)
            if len(matches) > 1:
                match_list.append(matches)
                all_matches.extend(matches)
            else:
                if matches[0] not in all_matches:
                    match_list.append(matches)
                    all_matches.extend(matches)

        for group in match_list:
            # Are there colocated instruments for this group?
            if len(group) > 1:
                # If so, loop over list of preferred instruments
                group_insts = [self[g].get_inst() for g in group]

                if large_dist:
                    tr = self[group[0]][0]
                    distance = (
                        gps2dist_azimuth(
                            tr.stats.coordinates.latitude,
                            tr.stats.coordinates.longitude,
                            origin.latitude,
                            origin.longitude,
                        )[0]
                        / 1000.0
                    )

                    if distance > dist_thresh:
                        preference = large_dist["preference"]

                # Loop over preferred instruments
                no_match = True
                for pref in preference:
                    # Is this instrument available in the group?
                    r = re.compile(pref[0:2])
                    inst_match = list(filter(r.match, group_insts))
                    if len(inst_match):
                        no_match = False
                        # Select index; if more than one, we just take the
                        # first one because we don't know any better
                        keep = inst_match[0]

                        # Label all non-selected streams in the group as failed
                        to_fail = group_insts
                        to_fail.remove(keep)
                        for tf in to_fail:
                            for st in self.select(
                                network=self[group[0]][0].stats.network,
                                station=self[group[0]][0].stats.station,
                                instrument=tf,
                            ):
                                for tr in st:
                                    tr.fail(f"Colocated with {keep} instrument.")

                        break
                if no_match:
                    # Fail all Streams in group
                    for g in group:
                        for tr in self[g]:
                            tr.fail(
                                "No instruments match entries in the "
                                "colocated instrument preference list for "
                                "this station."
                            )

    @classmethod
    def from_directory(cls, directory):
        """Create a StreamCollection instance from a directory of data.

        Args:
            directory (str):
                Directory of ground motion files (streams) to be read.
            use_default_config (bool):
                Use default ("production") config.

        Returns:
            StreamCollection instance.
        """
        config = get_config()
        streams, missed_files, errors = directory_to_streams(directory, config=config)

        # Might eventually want to include some of the missed files and
        # error info but don't have a sensible place to put it currently.
        return cls(streams, config=config)

    @classmethod
    def from_traces(cls, traces):
        """Create a StreamCollection instance from a list of traces.

        Args:
            traces (list):
                List of StationTrace objects.

        Returns:
            StreamCollection instance.
        """

        streams = [StationStream([tr]) for tr in traces]
        return cls(streams)

    def to_dataframe(self, origin, imcs=None, imts=None):
        """Get a summary dataframe of streams.

        Note: The PGM columns underneath each channel will be variable
        depending on the units of the Stream being passed in (velocity
        sensors can only generate PGV) and on the imtlist passed in by
        user. Spectral acceleration columns will be formatted as SA(0.3)
        for 0.3 second spectral acceleration, for example.

        Args:
            directory (str):
                Directory of ground motion files (streams).
            origin_dict (obspy):
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
                - DISTANCE Epicentral distance (km) (if epicentral lat/lon
                  provided)
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
        # dept for an origin object should be stored in meters
        origin = Origin(
            resource_id=origin["id"],
            latitude=origin["lat"],
            longitude=origin["lon"],
            time=origin["time"],
            depth=origin["depth"] * 1000,
        )

        if imcs is None:
            station_summary_imcs = DEFAULT_IMCS
        else:
            station_summary_imcs = imcs
        if imts is None:
            station_summary_imts = DEFAULT_IMTS
        else:
            station_summary_imts = imts

        if imcs is None:
            station_summary_imcs = DEFAULT_IMCS
        else:
            station_summary_imcs = imcs
        if imts is None:
            station_summary_imts = DEFAULT_IMTS
        else:
            station_summary_imts = imts

        subdfs = []
        for stream in streams:
            if not stream.passed:
                continue
            if len(stream) < 3:
                continue
            stream_summary = StationSummary.from_stream(
                stream, station_summary_imcs, station_summary_imts, origin
            )
            summary = stream_summary.summary
            subdfs += [summary]
        dataframe = pd.concat(subdfs, axis=0).reset_index(drop=True)

        return dataframe

    def __str__(self):
        """String summary of the StreamCollection."""
        summary = ""
        n = len(self.streams)
        summary += f"{n} StationStreams(s) in StreamCollection:\n"
        summary += f"    {self.n_passed} StationStreams(s) passed checks.\n"
        summary += f"    {self.n_failed} StationStreams(s) failed checks.\n"
        return summary

    def describe_string(self):
        """More verbose description of StreamCollection."""
        lines = [""]
        lines += [str(len(self.streams)) + " StationStreams(s) in StreamCollection:"]
        for stream in self:
            lines += [stream.__str__(indent=INDENT)]
        return "\n".join(lines)

    def describe(self):
        """Thin wrapper of describe_string() for printing to stdout"""
        stream_descript = self.describe_string()
        print(stream_descript)

    def __group_by_net_sta_inst(self):
        trace_list = []
        stream_params = gather_stream_parameters(self.streams)
        for st in self.streams:
            for tr in st:
                trace_list.append(tr)

        # Create a list of traces with matching net, sta.
        all_matches = []
        match_list = []
        for idx1, trace1 in enumerate(trace_list):
            if idx1 in all_matches:
                continue
            matches = [idx1]
            network = trace1.stats["network"]
            station = trace1.stats["station"]
            free_field = trace1.free_field
            # For instrument, use first two characters of the channel
            inst = trace1.stats["channel"][0:2]
            for idx2, trace2 in enumerate(trace_list):
                if idx1 != idx2 and idx1 not in all_matches:
                    if (
                        network == trace2.stats["network"]
                        and station == trace2.stats["station"]
                        and inst == trace2.stats["channel"][0:2]
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
                grouped_trace_list.append(trace_list[i])
            # some networks (e.g., Bureau of Reclamation, at the time of this
            # writing) use the location field to indicate different sensors at
            # (roughly) the same location. If we know this (as in the case of
            # BOR), we can use this to trim the stations into 3-channel
            # streams.
            streams = split_station(grouped_trace_list)
            streams = insert_stream_parameters(streams, stream_params)

            for st in streams:
                grouped_streams.append(st)

        self.streams = grouped_streams

    def __handle_duplicates(
        self,
        max_dist_tolerance,
        preference_order,
        process_level_preference,
        format_preference,
    ):
        """
        Removes duplicate data from the StreamCollection, based on the
        process level and format preferences.

        Args:
            max_dist_tolerance (float):
                Maximum distance tolerance for determining whether two streams
                are at the same location (in meters).
            preference_order (list):
                A list containing 'process_level', 'source_format',
                'starttime', 'npts', 'sampling_rate', 'location_code' in the
                desired order for choosing the preferred trace.
            process_level_preference (list):
                A list containing 'V0', 'V1', 'V2', with the order determining
                which process level is the most preferred (most preferred goes
                first in the list).
            format_preference (list):
                A list continaing strings of the file source formats (found
                in gmprocess.io). Does not need to list all of the formats.
                Example: ['cosmos', 'dmg'] indicates that cosmos files are
                preferred over dmg files.
        """

        # If arguments are None, check the config
        # If not in the config, use the default values at top of the file
        preferences = {
            "max_dist_tolerance": max_dist_tolerance,
            "preference_order": preference_order,
            "process_level_preference": process_level_preference,
            "format_preference": format_preference,
        }

        for key, val in preferences.items():
            if val is None:
                if self.config is None:
                    self.config = get_config()
                preferences[key] = self.config["duplicate"][key]

        stream_params = gather_stream_parameters(self.streams)

        traces = []
        for st in self.streams:
            for tr in st:
                traces.append(tr)
        preferred_traces = []

        for tr_to_add in traces:
            is_duplicate = False
            for tr_pref in preferred_traces:
                if are_duplicates(
                    tr_to_add, tr_pref, preferences["max_dist_tolerance"]
                ):
                    is_duplicate = True
                    break

            if is_duplicate:
                if (
                    choose_preferred(
                        tr_to_add,
                        tr_pref,
                        preferences["preference_order"],
                        preferences["process_level_preference"],
                        preferences["format_preference"],
                    )
                    == tr_to_add
                ):
                    preferred_traces.remove(tr_pref)
                    logging.info(
                        "Trace %s (%s) is a duplicate and "
                        "has been removed from the StreamCollection."
                        % (tr_pref.id, tr_pref.stats.standard.source_file)
                    )
                    preferred_traces.append(tr_to_add)
                else:
                    logging.info(
                        "Trace %s (%s) is a duplicate and "
                        "has been removed from the StreamCollection."
                        % (tr_to_add.id, tr_to_add.stats.standard.source_file)
                    )

            else:
                preferred_traces.append(tr_to_add)

        streams = [StationStream([tr]) for tr in preferred_traces]
        streams = insert_stream_parameters(streams, stream_params)
        self.streams = streams

    def get_status(self, status):
        """Returns a summary of the status of the streams in StreamCollection.

        If status='short': Returns a two column table, columns are "Failure
            Reason" and "Number of Records". Number of rows is the number of
            unique failure reasons.
        If status='net': Returns a three column table, columns are "Network",
            "Number Passed", and "Number Failed"; number of rows is the number
            of unique networks.
        If status='long': Returns a two column table, columns are "StationID"
            and "Failure Reason".

        Args:
            status (str):
                The status level (see description).

        Returns:
            If status='net': pandas.DataFrame
            If status='short' or status='long': pandas.Series
        """

        if status == "short":
            failure_reasons = pd.Series(
                [
                    next(tr for tr in st if tr.hasParameter("failure")).getParameter(
                        "failure"
                    )["reason"]
                    for st in self.streams
                    if not st.passed
                ],
                dtype=str,
            )
            failure_counts = failure_reasons.value_counts()
            failure_counts.name = "Number of Records"
            failure_counts.index.name = "Failure Reason"
            return failure_counts
        elif status == "net":
            failure_dict = {}
            for st in self.streams:
                net = st[0].stats.network
                if net not in failure_dict:
                    failure_dict[net] = {"Number Passed": 0, "Number Failed": 0}
                if st.passed:
                    failure_dict[net]["Number Passed"] += 1
                else:
                    failure_dict[net]["Number Failed"] += 1
            df = pd.DataFrame.from_dict(failure_dict).transpose()
            df.index.name = "Network"
            return df
        elif status == "long":
            failure_reasons = []
            for st in self.streams:
                if not st.passed:
                    first_failure = next(tr for tr in st if tr.hasParameter("failure"))
                    failure_reasons.append(
                        first_failure.getParameter("failure")["reason"]
                    )
                else:
                    failure_reasons.append("")
            sta_ids = [st.id for st in self.streams]
            failure_srs = pd.Series(
                index=sta_ids, data=failure_reasons, name="Failure reason"
            )
            failure_srs.index.name = "StationID"
            return failure_srs
        else:
            raise ValueError('Status must be "short", "net", or "long".')


def gather_stream_parameters(streams):
    """
    Helper function for gathering the stream parameters into a datastructure
    and sticking the stream tag into the trace stats dictionaries.

    Args:
        streams (list):
            list of StationStream objects.

    Returns:
        dict. Dictionary of the stream parameters.
    """
    stream_params = {}

    # Need to make sure that tag will be preserved; tag only really should
    # be created once a StreamCollection has been written to an ASDF file
    # and then read back in.
    for stream in streams:
        # we have stream-based metadata that we need to preserve
        if len(stream.parameters):
            stream_params[stream.get_id()] = stream.parameters

        # Tag is a StationStream attribute; If it does not exist, make it
        # an empty string
        if hasattr(stream, "tag"):
            tag = stream.tag
        else:
            tag = ""
        # Since we have to deconstruct the stream groupings each time, we
        # need to stick the tag into the trace stats dictionary temporarily
        for trace in stream:
            tr = trace
            tr.stats.tag = tag

    return stream_params


def insert_stream_parameters(streams, stream_params):
    """Helper function for inserting the stream parameters back to the streams.

    Args:
        streams (list):
            list of StationStream objects.
        stream_params (dict):
            Dictionary of stream parameters.

    Returns:
        list of StationStream objects with stream parameters.
    """
    for st in streams:
        if len(st):
            sid = st.get_id()
            # put stream parameters back in
            if sid in stream_params:
                st.parameters = stream_params[sid].copy()

            # Put tag back as a stream attribute, assuming that the
            # tag has stayed the same through the grouping process
            if st[0].stats.tag:
                st.tag = st[0].stats.tag

    return streams


def split_station(grouped_trace_list):
    if grouped_trace_list[0].stats.network in NETWORKS_USING_LOCATION:
        streams_dict = {}
        for trace in grouped_trace_list:
            if trace.stats.location in streams_dict:
                streams_dict[trace.stats.location] += trace
            else:
                streams_dict[trace.stats.location] = StationStream(traces=[trace])
        streams = list(streams_dict.values())
    else:
        streams = [StationStream(traces=grouped_trace_list)]
    return streams


def are_duplicates(tr1, tr2, max_dist_tolerance):
    """Check if traces are duplicates.

    Determines whether two StationTraces are duplicates by checking the
    station, channel codes, and the distance between them.

    Args:
        tr1 (StationTrace):
            1st trace.
        tr2 (StationTrace):
            2nd trace.
        max_dist_tolerance (float):
            Maximum distance tolerance for determining whether two streams
            are at the same location (in meters).

    Returns:
        bool. True if traces are duplicates, False otherwise.
    """
    orientation_codes = set()
    for tr in [tr1, tr2]:
        if tr.stats.channel[2] in ["1", "N"]:
            orientation_codes.add("1")
        elif tr.stats.channel[2] in ["2", "E"]:
            orientation_codes.add("2")
        else:
            orientation_codes.add("Z")

    # First, check if the ids match (net.sta.loc.cha)
    if tr1.id[:-1] == tr2.id[:-1] and len(orientation_codes) == 1:
        return True
    # If not matching IDs, check the station, instrument code, and distance
    else:
        distance = gps2dist_azimuth(
            tr1.stats.coordinates.latitude,
            tr1.stats.coordinates.longitude,
            tr2.stats.coordinates.latitude,
            tr2.stats.coordinates.longitude,
        )[0]
        if (
            tr1.stats.station == tr2.stats.station
            and tr1.stats.channel[:2] == tr2.stats.channel[:2]
            and len(orientation_codes) == 1
            and distance < max_dist_tolerance
        ):
            return True
        else:
            return False


def choose_preferred(
    tr1, tr2, preference_order, process_level_preference, format_preference
):
    """Determines which trace is preferred. Returns the preferred trace.

    Args:
        tr1 (StationTrace):
            1st trace.
        tr2 (StationTrace):
            2nd trace.
        preference_order (list):
            A list containing 'process_level', 'source_format', 'starttime',
            'npts', 'sampling_rate', 'location_code' in the desired order
            for choosing the preferred trace.
        process_level_preference (list):
            A list containing 'V0', 'V1', 'V2', with the order determining
            which process level is the most preferred (most preferred goes
            first in the list).
        format_preference (list):
            A list continaing strings of the file source formats (found
            in gmprocess.io). Does not need to list all of the formats.
            Example: ['cosmos', 'dmg'] indicates that cosmos files are
            preferred over dmg files.

    Returns:
        The preferred trace (StationTrace).
    """
    traces = [tr1, tr2]
    for pref in preference_order:
        if pref == "process_level":
            tr_prefs = [
                process_level_preference.index(
                    REV_PROCESS_LEVELS[tr.stats.standard.process_level]
                )
                for tr in traces
            ]
        elif pref == "source_format":
            if all(
                [tr.stats.standard.source_format in format_preference for tr in traces]
            ):
                tr_prefs = [
                    format_preference.index(tr.stats.standard.source_format)
                    for tr in traces
                ]
            else:
                continue
        elif pref == "starttime":
            tr_prefs = [tr.stats.starttime == UTCDateTime(0) for tr in traces]
        elif pref == "npts":
            tr_prefs = [1 / tr.stats.npts for tr in traces]
        elif pref == "sampling_rate":
            tr_prefs = [1 / tr.stats.sampling_rate for tr in traces]
        elif pref == "location_code":
            sorted_codes = sorted([tr.stats.location for tr in traces])
            tr_prefs = [
                sorted_codes.index(tr.stats.location)
                if tr.stats.location != "--"
                else np.nan
                for tr in traces
            ]

        if len(set(tr_prefs)) != 1:
            return traces[np.nanargmin(tr_prefs)]
    return tr1
