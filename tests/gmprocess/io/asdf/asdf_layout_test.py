#!/usr/bin/env pytest

# stdlib imports
import os
import tempfile
import shutil

# third party imports
import h5py

# local imports
from gmprocess.io.read import read_data
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.asdf.core import write_asdf
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.config import update_config, get_config
from gmprocess.utils.constants import TEST_DATA_DIR

CONFIG = get_config()


def generate_workspace():
    """Generate simple HDF5 with ASDF layout for testing."""
    EVENTID = "us1000778i"
    LABEL = "ptest"
    datafiles, event = read_data_dir("geonet", EVENTID, "*.V1A")

    tdir = tempfile.mkdtemp()
    tfilename = os.path.join(tdir, "workspace.h5")

    raw_data = []
    for dfile in datafiles:
        raw_data += read_data(dfile)
    write_asdf(tfilename, raw_data, event, label="unprocessed")
    del raw_data

    config = update_config(
        os.path.join(TEST_DATA_DIR, "config_min_freq_0p2.yml"), CONFIG
    )

    workspace = StreamWorkspace.open(tfilename)
    raw_streams = workspace.getStreams(EVENTID, labels=["unprocessed"], config=config)
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
    LAYOUT_FILENAME = "asdf_layout.txt"

    tfilename = setup_module.tfilename
    h5 = h5py.File(tfilename, "r")

    testroot = TEST_DATA_DIR / "asdf"
    layout_abspath = os.path.join(testroot, LAYOUT_FILENAME)
    with open(layout_abspath, "r", encoding="utf-8") as fin:
        lines = fin.readlines()
        for line in lines:
            assert line.strip() in h5
    h5.close()
    return


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_layout()
