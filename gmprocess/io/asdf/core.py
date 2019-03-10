# third party imports
import h5py

# local imports
from .stream_workspace import StreamWorkspace

TIMEPAT = '[0-9]{4}-[0-9]{2}-[0-9]{2}T'


def is_asdf(filename):
    """Verify that the input file is an ASDF file.

    Args:
        filename (str): Path to candidate ASDF file.

    Returns:
        bool: True if ASDF, False if not.
    """
    try:
        f = h5py.File(filename, 'r')
        if 'AuxiliaryData' in f:
            return True
        else:
            return False
    except OSError:
        return False
    return True


def read_asdf(filename, label=None):
    """Read Streams of data (complete with processing metadata) from an ASDF file.

    Args:
        filename (str):
            Path to valid ASDF file.
        label (str): Optional processing label to filter streams.

    Returns:
        list:
            List of StationStreams containing processing
            and channel metadata.
    """
    workspace = StreamWorkspace.open(filename)
    eventids = workspace.getEventIds()
    allstreams = []
    for eventid in eventids:
        if label is not None:
            tags = workspace.getStreamTags(eventid)
            newtags = []
            for tag in tags:
                if label in name:
                    newtags.append(tag)
        else:
            newtags = None
        streams = workspace.getStreams(eventid, tags=newtags)
        allstreams += streams

    workspace.close()
    return allstreams


def write_asdf(filename, streams, event, label=None):
    """Write a number of streams (raw or processed) into an ASDF file.

    Args:
        filename (str):
            Path to the HDF file that should contain stream data.
        streams (list):
            List of StationStream objects that should be written into the file.
        event (Obspy Event or dict):
            Obspy event object or dict (see get_event_dict())
        label (str):
            Label to append to all streams being added to ASDF file.
    """
    workspace = StreamWorkspace(filename)
    workspace.addStreams(event, streams, label=label)
    workspace.close()
