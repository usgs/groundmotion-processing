#!/usr/bin/env pytest

# stdlib imports
import os
import tempfile
import shutil

# third party imports
import h5py

# local imports
from gmprocess.io.read import read_data
from gmprocess.io.test_utils import read_data_dir
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.processing import process_streams
from gmprocess.io.asdf.core import write_asdf
from gmprocess.config import get_config


def generate_workspace():
    """Generate simple HDF5 with ASDF layout for testing.
    """
    PCOMMANDS = [
        'assemble',
        'process',
        ]
    EVENTID = 'us1000778i'
    LABEL = 'ptest'
    datafiles, event = read_data_dir('geonet', EVENTID, '*.V1A')

    tdir = tempfile.mkdtemp()
    tfilename = os.path.join(tdir, 'workspace.h5')

    raw_data = []
    for dfile in datafiles:
        raw_data += read_data(dfile)
    write_asdf(tfilename, raw_data, event, label="unprocessed")
    del raw_data

    config = get_config()
    workspace = StreamWorkspace.open(tfilename)
    raw_streams = workspace.getStreams(EVENTID, labels=['unprocessed'])
    pstreams = process_streams(raw_streams, event, config=config)
    workspace.addStreams(event, pstreams, label=LABEL)
    workspace.calcMetrics(event.id, labels=[LABEL], config=config)

    return tfilename


def setup_module(module):
    setup_module.tfilename = generate_workspace()
    return


def teardown_module(module):
    tdir = os.path.split(setup_module.tfilename)[0]
    shutil.rmtree(tdir)
    return


def test_layout():
    LAYOUT_FILENAME = 'layout.txt'
    LAYOUT_TYPES = {
        'group': h5py.Group,
        'dataset': h5py.Dataset,
    }
    
    tfilename = setup_module.tfilename
    h5 = h5py.File(tfilename, "r")

    with open(LAYOUT_FILENAME, "r") as fin:
        lines = fin.readlines()
        for line in lines:
            itype, item = line.split()
            #assert item in h5
            #assert LAYOUT_TYPES[itype] == type(h5[item])
    h5.close()
    return


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_layout()
