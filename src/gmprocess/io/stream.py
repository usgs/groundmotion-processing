#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import glob
import os

# third party imports
import pandas as pd

# local imports
from gmprocess.io.read import read_data
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.core.streamcollection import StreamCollection


DEFAULT_IMTS = ["PGA", "PGV", "SA(0.3)", "SA(1.0)", "SA(3.0)"]
DEFAULT_IMCS = ["GREATER_OF_TWO_HORIZONTALS", "CHANNELS"]


def directory_to_dataframe(directory, imcs=None, imts=None, origin=None, process=True):
    """Extract peak ground motions from list of Stream objects.
    Note: The PGM columns underneath each channel will be variable
    depending on the units of the Stream being passed in (velocity
    sensors can only generate PGV) and on the imtlist passed in by
    user. Spectral acceleration columns will be formatted as SA(0.3)
    for 0.3 second spectral acceleration, for example.

    Args:
        directory (str): Directory of ground motion files (streams).
        imcs (list): Strings designating desired components to create
                in table.
        imts (list): Strings designating desired PGMs to create
                in table.
        origin (obspy.core.event.Origin): Defines the focal time and
                geographical location of an earthquake hypocenter.
                Default is None.
        process (bool): Process the stream using the config file.

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
            - HN2 North-south channel (or H2) (multi-index with pgm columns):
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
    streams = []
    for filepath in glob.glob(os.path.join(directory, "*")):
        streams += read_data(filepath)
    grouped_streams = StreamCollection(streams)

    dataframe = streams_to_dataframe(
        grouped_streams, imcs=imcs, imts=imts, origin=origin
    )
    return dataframe


def streams_to_dataframe(streams, imcs=None, imts=None, event=None):
    """Extract peak ground motions from list of processed StationStream
    objects.

    Note: The PGM columns underneath each channel will be variable
    depending on the units of the Stream being passed in (velocity
    sensors can only generate PGV) and on the imtlist passed in by
    user. Spectral acceleration columns will be formatted as SA(0.3)
    for 0.3 second spectral acceleration, for example.

    Args:
        streams (StreamCollection):
            List of streams as a StreamCollection object.
        imcs (list):
            Strings designating desired components to create in table.
        imts (list):
            Strings designating desired PGMs to create in table.
        event (ScalarEvent): Defines the focal time,
                geographic location, and magnitude of an earthquake hypocenter.
                Default is None.

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
            - HN2 North-south channel (or H2) (multi-index with pgm columns):
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
            stream, station_summary_imcs, station_summary_imts, event
        )
        summary = stream_summary.summary
        subdfs += [summary]
    dataframe = pd.concat(subdfs, axis=0).reset_index(drop=True)

    return dataframe


def _match_traces(trace_list):
    # Create a list of traces with matching net, sta.
    all_matches = []
    match_list = []
    for idx1, trace1 in enumerate(trace_list):
        if idx1 in all_matches:
            continue
        matches = [idx1]
        network = trace1.stats["network"]
        station = trace1.stats["station"]
        for idx2, trace2 in enumerate(trace_list):
            if idx1 != idx2 and idx1 not in all_matches:
                if (
                    network == trace2.stats["network"]
                    and station == trace2.stats["station"]
                ):
                    matches.append(idx2)
        if len(matches) > 1:
            match_list.append(matches)
            all_matches.extend(matches)
        else:
            if matches[0] not in all_matches:
                match_list.append(matches)
                all_matches.extend(matches)
    return match_list
