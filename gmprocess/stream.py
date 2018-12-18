# stdlib imports
import warnings

# third party imports
import numpy as np
from obspy.core.stream import Stream
from obspy.geodetics import gps2dist_azimuth

# local imports
from gmprocess.process import filter_detrend
from gmprocess.metrics.station_summary import StationSummary


GAL_TO_PCTG = 1 / (9.8)

FILTER_FREQ = 0.02
CORNERS = 4

DEFAULT_IMTS = ['PGA', 'PGV', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)']


def group_channels(streams):
    """Consolidate streams for the same event.

    Checks to see if there are channels for one event in different streams, and
    groups them into one stream. Then streams are checked for duplicate
    channels (traces).

    Args:
        streams (list): List of Stream objects.
    Returns:
        list: List of Stream objects.
    """
    # Return the original stream if there is only one
    if len(streams) <= 1:
        return streams

    # Get the all traces
    trace_list = []
    for stream in streams:
        for trace in stream:
            trace_list += [trace]

    # Create a list of duplicate traces and event matches
    duplicate_list = []
    match_list = []
    for idx1, trace1 in enumerate(trace_list):
        matches = []
        network = trace1.stats['network']
        station = trace1.stats['station']
        starttime = trace1.stats['starttime']
        endtime = trace1.stats['endtime']
        channel = trace1.stats['channel']
        location = trace1.stats['location']
        if 'units' in trace1.stats.standard:
            units = trace1.stats.standard['units']
        else:
            units = ''
        if 'process_level' in trace1.stats.standard:
            process_level = trace1.stats.standard['process_level']
        else:
            process_level = ''
        data = np.asarray(trace1.data)
        for idx2, trace2 in enumerate(trace_list):
            if idx1 != idx2 and idx1 not in duplicate_list:
                event_match = False
                duplicate = False
                if data.shape == trace2.data.shape:
                    try:
                        same_data = ((data == np.asarray(trace2.data)).all())
                    except AttributeError:
                        same_data = (data == np.asarray(trace2.data))
                else:
                    same_data = False
                if 'units' in trace2.stats.standard:
                    units2 = trace2.stats.standard['units']
                else:
                    units2 = ''
                if 'process_level' in trace2.stats.standard:
                    process_level2 = trace2.stats.standard['process_level']
                else:
                    process_level2 = ''
                if (
                    network == trace2.stats['network'] and
                    station == trace2.stats['station'] and
                    starttime == trace2.stats['starttime'] and
                    endtime == trace2.stats['endtime'] and
                    channel == trace2.stats['channel'] and
                    location == trace2.stats['location'] and
                    units == units2 and
                    process_level == process_level2 and
                    same_data
                ):
                    duplicate = True
                elif (
                    network == trace2.stats['network'] and
                    station == trace2.stats['station'] and
                    starttime == trace2.stats['starttime'] and
                    location == trace2.stats['location'] and
                    units == units2 and
                    process_level == process_level2
                ):
                    event_match = True
                if duplicate:
                    duplicate_list += [idx2]
                if event_match:
                    matches += [idx2]
        match_list += [matches]

    # Create an updated list of streams
    streams = []
    for idx, matches in enumerate(match_list):
        stream = Stream()
        grouped = False
        for match_idx in matches:
            if match_idx not in duplicate_list:
                if idx not in duplicate_list:
                    stream.append(trace_list[match_idx])
                    duplicate_list += [match_idx]
                    grouped = True
        if grouped:
            stream.append(trace_list[idx])
            duplicate_list += [idx]
            streams += [stream]

    # Check for ungrouped traces
    for idx, trace in enumerate(trace_list):
        if idx not in duplicate_list:
            stream = Stream()
            streams += [stream.append(trace)]
            warnings.warn('One channel stream:\n%s' % (stream), Warning)

    return streams
