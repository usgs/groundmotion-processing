#!/usr/bin/env python

import os.path
import glob
import shutil
import numpy as np
from gmprocess.io.asdf.core import is_asdf, read_asdf, write_asdf
from gmprocess.io.asdf.asdf_utils import inventory_from_stream, get_event_info
from gmprocess.io.read import read_data
from gmprocess.stream import group_channels
from gmprocess.processing import process_config
import tempfile


def dummy_test():
    # where is this script?
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, '..', '..', '..', 'data', 'asdf')
    knetdir = os.path.join(homedir, '..', '..', '..', 'data', 'knet')
    tdir = tempfile.mkdtemp()
    eventid = 'us2000cnnl'
    try:
        tfile = os.path.join(tdir, 'test.hdf')

        streams = []
        knetfiles = glob.glob(os.path.join(knetdir, 'AO*'))
        for knetfile in knetfiles:
            stream = read_data(knetfile)
            streams.append(stream)

        raw_streams = group_channels(streams)

        # test the inventory_from_stream method
        inventory = inventory_from_stream(raw_streams[0])
        sfile = os.path.join(tdir, 'station.xml')
        inventory.write(sfile, format="stationxml", validate=True)

        process_streams = []
        for raw_stream in raw_streams:
            process_stream = process_config(raw_stream)
            process_streams.append(process_stream)

        process_streams = group_channels(process_streams)

        all_streams = raw_streams + process_streams

        event = get_event_info(eventid)

        write_asdf(tfile, all_streams, event=event)

        assert is_asdf(tfile)

        streams = read_asdf(tfile)
    except:
        assert 1 == 2
    finally:
        shutil.rmtree(tdir)


if __name__ == '__main__':
    dummy_test()
