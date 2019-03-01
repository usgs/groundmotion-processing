import pyasdf
import h5py
import numpy as np

from .asdf_utils import (inventory_from_stream,
                         stats_from_inventory,
                         get_event_info)
from .provenance import get_provenance, extract_provenance

from gmprocess.stationtrace import StationTrace
from gmprocess.stationstream import StationStream


def is_asdf(filename):
    try:
        f = h5py.File(filename, 'r')
        if 'AuxiliaryData' in f:
            return True
        else:
            return False
    except OSError:
        return False
    return True


def read_asdf(filename):
    """Read Streams of data (complete with processing metadata) from an ASDF file.

    Args:
        filename (str): Path to valid ASDF file.

    Returns:
        list: List of Streams containing processing and channel metadata.
    """
    ds = pyasdf.ASDFDataSet(filename)
    streams = []
    for waveform in ds.waveforms:
        inventory = waveform['StationXML']
        tags = waveform.get_waveform_tags()
        for tag in tags:
            tstream = waveform[tag].copy()
            traces = []
            for ttrace in tstream:
                trace = StationTrace(data=ttrace.data,
                                     header=ttrace.stats,
                                     inventory=inventory)
                if tag in ds.provenance.list():
                    provdoc = ds.provenance[tag]
                    trace = extract_provenance(trace, provdoc)
                traces.append(trace)
            stream = StationStream(traces=traces)
            streams.append(stream)
    return streams


def write_asdf(filename, streams, event=None):
    """Write a number of streams (raw or processed) into an ASDF file.

    Args:
        filename (str): 
            Path to the HDF file that should contain stream data.
        streams (list): 
            List of StationStream objects that should be written into the file.
        event (Obspy Event or dict): 
            Obspy event object or dict (see get_event_dict())
    """
    ds = pyasdf.ASDFDataSet(filename, compression="gzip-3")

    # to allow for multiple processed versions of the same Stream
    # let's keep a dictionary of stations and sequence number.
    station_dict = {}

    # add event information to the dataset
    eventobj = None
    if event is not None:
        if isinstance(event, dict):
            event = get_event_info(event)
        ds.add_quakeml(event)
        eventobj = ds.events[0]

    # add the streams and associated metadata for each one
    for stream in streams:
        station = stream[0].stats['station']
        # is this a raw file? Check the trace for provenance info.
        is_raw = not len(stream[0].getProvenanceKeys())
        if is_raw:
            tag = 'raw_recording'
            level = 'raw'
        else:
            if station.lower() in station_dict:
                station_sequence = station_dict[station.lower()] + 1
            else:
                station_sequence = 1
            station_dict[station.lower()] = station_sequence
            tag = '%s_%i' % (station.lower(), station_sequence)
            level = 'processed'
        ds.add_waveforms(stream, tag=tag, event_id=eventobj)

        if level == 'processed':
            provdocs = get_provenance(stream)
            for provdoc in provdocs:
                ds.add_provenance_document(provdoc, name=tag)

        inventory = stream.getInventory()
        ds.add_stationxml(inventory)

    # no close or other method for ASDF data sets?
    # this may force closing of the file...
    del ds
