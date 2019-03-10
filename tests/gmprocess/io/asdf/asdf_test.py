#!/usr/bin/env python

import os.path
import shutil
import logging
import time

import numpy as np
from gmprocess.io.asdf.core import is_asdf, read_asdf, write_asdf
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.read import read_data
from gmprocess.processing import process_streams
from gmprocess.config import get_config
from gmprocess.io.test_utils import read_data_dir
from gmprocess.event import get_event_object
import tempfile


def test_asdf():
    eventid = 'us1000778i'
    datafiles, origin = read_data_dir('geonet', eventid, '*.V1A')
    event = get_event_object(origin)
    tdir = tempfile.mkdtemp()
    try:
        config = get_config()
        tfile = os.path.join(tdir, 'test.hdf')
        raw_streams = []
        for dfile in datafiles:
            raw_streams += read_data(dfile)

        write_asdf(tfile, raw_streams, event)

        out_streams = read_asdf(tfile)
        x = 1

    except Exception:
        assert 1 == 2
    finally:
        shutil.rmtree(tdir)


if __name__ == '__main__':
    test_asdf()
