#!/usr/bin/env pytest

# stdlib imports
import os
import tempfile
import shutil
import pkg_resources

# third party imports
import h5py

# local imports
from gmprocess.io.read import read_data
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.asdf.core import write_asdf
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.config import update_config


datapath = os.path.join('data', 'testdata')
datadir = pkg_resources.resource_filename('gmprocess', datapath)


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

    config = update_config(os.path.join(datadir, 'config_min_freq_0p2.yml'))

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
    LAYOUT_FILENAME = 'asdf_layout.txt'
    LAYOUT_TYPES = {
        'group': h5py.Group,
        'dataset': h5py.Dataset,
    }

    tfilename = setup_module.tfilename
    h5 = h5py.File(tfilename, "r")

    layout_path = os.path.join('data', 'testdata', 'asdf')
    testroot = pkg_resources.resource_filename('gmprocess', layout_path)
    layout_abspath = os.path.join(testroot, LAYOUT_FILENAME)
    with open(layout_abspath, "r", encoding='utf-8') as fin:
        lines = fin.readlines()
        for line in lines:
            assert line.strip() in h5
    h5.close()
    return


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_layout()
