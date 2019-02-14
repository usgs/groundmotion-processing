import pyasdf
import h5py
import numpy as np


def is_asdf(filename):
    try:
        f = h5py.File(filename,'r')  
        if 'AuxiliaryData' in f:
            return True
        else:
            return False
    except OSError:
        return False
    return True


def read_asdf(filename):
    pass


def write_asdf(filename, streams, event=None):
    """Write a number of streams (raw or processed) into an ASDF file.

    Args:
        filename (str): Path to the HDF file that should contain stream data.
        streams (list): List of Obspy Streams that should be written into the file.
        event (Obspy Event): Obspy event object.
    """
    ds = pyasdf.ASDFDataSet(filename, compression="gzip-3")

    # add event information to the dataset
    eventobj = None
    if event is not None:
        ds.add_quakeml(event)
        eventobj = ds.events[0]

    # add the streams and associated metadata for each one
    for stream in streams:
        station = stream[0].stats['station']
        # is this a raw file? Check the trace.stats for a 'processing_parameters' dictionary.
        is_raw = 'processing_parameters' not in stream[0].stats
        if is_raw:
            tag = 'raw_recording'
            level = 'raw'
        else:
            tag = '%s_1' % station.lower()
            level = 'processed'
        ds.add_waveforms(stream, tag=tag, event_id=event)
        stats_extras = ['coordinates', 'standard',
                        'format_specific', 'processing_parameters']
        for trace in stream:
            network = trace.stats['network']
            channel = trace.stats['channel']
            for extra in stats_extras:
                if extra not in trace.stats:
                    continue
                path = '%s_%s/%s/%s/%s' % (network, station, channel, level, extra)
                data_type_str = '%sXXX%s' % (network.upper(), station)
                try:
                    ds.add_auxiliary_data(np.zeros((1,1)),
                                        data_type=data_type_str,
                                        path=path,
                                        parameters=dict(trace.stats[extra]))
                except Exception as e:
                    x = 1

    # no close or other method for ASDF data sets?
    # this may force closing of the file...
    del ds
