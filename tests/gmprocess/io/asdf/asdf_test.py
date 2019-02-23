#!/usr/bin/env python

import os.path
import glob
import shutil
import numpy as np
from gmprocess.io.asdf.core import is_asdf, read_asdf, write_asdf
from gmprocess.io.asdf.asdf_utils import (inventory_from_stream,
                                          get_event_info, get_event_dict)
from gmprocess.io.read import read_data
from gmprocess.stream import group_channels
from gmprocess.processing import process_streams
from gmprocess.config import get_config
import tempfile


def dummy_test():
    # where is this script?
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, '..', '..', '..', 'data', 'asdf')
    netdir = os.path.join(homedir, '..', '..', '..', 'data', 'geonet')
    tdir = tempfile.mkdtemp()
    eventid = 'us2000cnnl'
    try:
        tfile = os.path.join(tdir, 'test.hdf')

        streams = []
        netfile = os.path.join(netdir, '20161113_110259_WTMC_20.V1A')
        stream = read_data(netfile)
        streams.append(stream)

        # test the inventory_from_stream method
        inventory = inventory_from_stream(streams[0])
        sfile = os.path.join(tdir, 'station.xml')
        inventory.write(sfile, format="stationxml", validate=True)

        config = get_config()
        processing = config['processing']
        idx = -1
        for i in range(0, len(processing)):
            process = processing[i]
            if 'remove_response' in process:
                idx = i
                break
        processing.pop(idx)

        origin = get_event_dict(eventid)

        processed_streams = process_streams(streams, origin, config=config)

        all_streams = streams + processed_streams

        write_asdf(tfile, all_streams, event=origin)

        assert is_asdf(tfile)

        streams = read_asdf(tfile)
    except:
        assert 1 == 2
    finally:
        shutil.rmtree(tdir)


if __name__ == '__main__':
    dummy_test()
