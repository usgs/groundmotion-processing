# stdlib imports
import glob
import os

# third party imports
import numpy as np
from obspy.geodetics import gps2dist_azimuth
from obspy.core.event import Origin
import pandas as pd

# local imports
from gmprocess.io.read import read_data
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.streamcollection import StreamCollection


DEFAULT_IMTS = ['PGA', 'PGV', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)']
DEFAULT_IMCS = ['GREATER_OF_TWO_HORIZONTALS', 'CHANNELS']


def directory_to_dataframe(directory, imcs=None, imts=None, epi_dist=None,
                           event_time=None, lat=None, lon=None, process=True):
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
        epi_dist (float): Epicentral distance for processsing. If not included,
                but the lat and lon are, the distance will be calculated.
        event_time (float): Time of the event, used for processing.
        lat (float): Epicentral latitude. Epicentral distance calculation.
        lon (float): Epicentral longitude. Epicentral distance calculation.
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
            - DISTANCE Epicentral distance (km) (if epicentral lat/lon provided)
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
        grouped_streams, imcs=imcs, imts=imts, epi_dist=epi_dist,
        event_time=event_time, lat=lat, lon=lon, process=process)
    return dataframe


def streams_to_dataframe(streams, imcs=None, imts=None,
                         epi_dist=None, event_time=None,
                         lat=None, lon=None):
    """Extract peak ground motions from list of processed StationStream objects.

    Note: The PGM columns underneath each channel will be variable
    depending on the units of the Stream being passed in (velocity
    sensors can only generate PGV) and on the imtlist passed in by
    user. Spectral acceleration columns will be formatted as SA(0.3)
    for 0.3 second spectral acceleration, for example.

    Args:
        directory (str):
            Directory of ground motion files (streams).
        imcs (list):
            Strings designating desired components to create in table.
        imts (list):
            Strings designating desired PGMs to create in table.
        epi_dist (float):
            Epicentral distance for processsing. If not included, but the lat
            and lon are, the distance will be calculated.
        event_time (float):
            Time of the event, used for processing.
        lat (float):
            Epicentral latitude. Epicentral distance calculation.
        lon (float):
            Epicentral longitude. Epicentral distance calculation.

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

    if lat is not None:
        columns = ['STATION', 'NAME', 'SOURCE',
                   'NETID', 'LAT', 'LON', 'DISTANCE']
    else:
        columns = ['STATION', 'NAME', 'SOURCE', 'NETID', 'LAT', 'LON']
    station_pgms = []
    imcs = []
    imts = []
    idx = 0
    meta_data = []
    for stream in streams:
        if not stream.passed:
            continue
        if len(stream) < 3:
            continue
        # set meta_data
        row = np.zeros(len(columns), dtype=list)
        row[0] = stream[0].stats['station']
        name_str = stream[0].stats['standard']['station_name']
        row[1] = name_str
        source = stream[0].stats.standard['source']
        row[2] = source
        row[3] = stream[0].stats['network']
        latitude = stream[0].stats['coordinates']['latitude']
        row[4] = latitude
        longitude = stream[0].stats['coordinates']['longitude']
        row[5] = longitude
        if lat is not None:
            dist, _, _ = gps2dist_azimuth(
                lat, lon, latitude, longitude)
            row[6] = dist / 1000
            if epi_dist is None:
                epi_dist = dist / 1000
        meta_data.append(row)
        origin = Origin(latitude=lat, longitude=lon)
        stream_summary = StationSummary.from_stream(
            stream, station_summary_imcs, station_summary_imts, origin)
        pgms = stream_summary.pgms
        station_pgms += [pgms]
        imcs += stream_summary.components
        imts += stream_summary.imts

    meta_data = np.array(meta_data)
    if not len(meta_data):
        dataframe = pd.DataFrame()
    else:
        num_streams, _ = meta_data.shape
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
                    if imc in station[imt]:
                        pgm_data[idx][subindex] = station[imt][imc]
                        subindex += 1
        pgm_dataframe = pd.DataFrame(pgm_data, columns=pgm_columns)

        dataframe = pd.concat([meta_dataframe, pgm_dataframe], axis=1)

    return dataframe


def _match_traces(trace_list):
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
    return match_list
