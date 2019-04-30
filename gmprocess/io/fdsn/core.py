#!/usr/bin/env python

# stdlib imports
import os
import logging

# third party
from obspy.core.stream import read
from obspy import read_inventory

# local imports
from gmprocess.stationtrace import StationTrace
from gmprocess.stationstream import StationStream

IGNORE_FORMATS = ['KNET']


def _get_station_file(filename, stream):
    filebase, fname = os.path.split(filename)
    fmt = '%s.%s.xml'
    tpl = (stream[0].stats.network, stream[0].stats.station)
    station_id = fmt % tpl
    xmlfile = os.path.join(filebase, station_id)
    return xmlfile


def is_fdsn(filename):
    """Check to see if file is a format supported by Obspy (not KNET).

    Args:
        filename (str): Path to possible Obspy format.
    Returns:
        bool: True if obspy supported, otherwise False.
    """
    logging.debug("Checking if format is Obspy.")
    if not os.path.isfile(filename):
        return False
    try:
        stream = read(filename)
        if stream[0].stats._format in IGNORE_FORMATS:
            return False
        xmlfile = _get_station_file(filename, stream)
        if not os.path.isfile(xmlfile):
            return False
        return True
    except Exception:
        return False

    return False


def read_fdsn(filename):
    """Read Obspy data file (SAC, MiniSEED, etc).

    Args:
        filename (str):
            Path to data file.
        kwargs (ref):
            Other arguments will be ignored.
    Returns:
        Stream: StationStream object.
    """
    logging.debug("Starting read_fdsn.")
    if not is_fdsn(filename):
        raise Exception('%s is not a valid Obspy file format.' % filename)

    streams = []
    tstream = read(filename)
    xmlfile = _get_station_file(filename, tstream)
    inventory = read_inventory(xmlfile)
    traces = []
    for ttrace in tstream:
        trace = StationTrace(data=ttrace.data,
                             header=ttrace.stats,
                             inventory=inventory)
        head, tail = os.path.split(filename)
        trace.stats['standard']['source_file'] = tail or os.path.basename(head)
        traces.append(trace)
    stream = StationStream(traces=traces)
    streams.append(stream)

    return streams
