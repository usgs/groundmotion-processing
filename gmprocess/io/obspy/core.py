# stdlib imports
import os.path
import json

# third party libraries
from obspy.core import read
from obspy.core.trace import Trace
from obspy.core.stream import Stream
import numpy as np


def is_obspy(filename):
    """Check to see if file is a ObsPy supported (corrected, in acc.) strong motion file.

    Args:
        filename (str): Path to possible ObsPy supported corrected data file.
    Returns:
        bool: True if Obspy supported , False otherwise.
    """
    try:
        _ = read(filename)
        return True
    except Exception:
        return False


def read_obspy(filename):
    """Read ObsPy supported strong motion file.
    Args:
        filename (str): Path to possible ObsPy supported data file.
        kwargs (ref):
            any_structure (bool): Read data from any type of structure,
                raise Exception if False and structure type is not free-field.
            Other arguments will be ignored.
    Returns:
        Stream: Obspy Stream containing one channel of acceleration
            data (cm/s**2).
    """
    if not is_obspy(filename):
        raise Exception('%s is not an Obspy supported file format.' % filename)

    # find the accompanying geojson or station.xml file
    # just json for now
    fbase, _ = os.path.splitext(filename)
    jsonfile = fbase + '.json'
    if not os.path.isfile(jsonfile):
        fmt = 'The Obspy reader requires an accompanying JSON file %s.'
        raise Exception(fmt % jsonfile)

    jdict = json.load(open(jsonfile, 'rt'))

    jdict = _denull_stats(jdict)

    tstream = read(filename)
    traces = []
    for ttrace in tstream:
        channel = ttrace.stats['channel']
        stats = jdict['properties'][channel]
        trace = Trace(ttrace.data, header=stats)
        traces.append(trace)

    stream = Stream(traces)

    return stream


def _denull_stats(jdict):
    for key, value in jdict.items():
        if isinstance(value, (dict)):
            value = _denull_stats(value)
            jdict[key] = value
        elif value == 'null':
            jdict[key] = np.nan
        else:
            jdict[key] = value
    return jdict
