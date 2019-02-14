#!/usr/bin/env python

import os.path
import glob
import shutil
import numpy as np
from gmprocess.io.asdf.core import is_asdf, read_asdf, write_asdf
from gmprocess.io.read import read_data
from gmprocess.stream import group_channels
from gmprocess.process import process_config
import tempfile


def dummy_test():
    # where is this script?
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, '..', '..', '..', 'data', 'asdf')
    knetdir = os.path.join(homedir, '..', '..', '..', 'data', 'knet')
    tdir = tempfile.mkdtemp()
    try:
        tfile = os.path.join(tdir, 'test.hdf')

        streams = []
        knetfiles = glob.glob(os.path.join(knetdir, 'AO*'))
        for knetfile in knetfiles:
            stream = read_data(knetfile)
            streams.append(stream)

        raw_streams = group_channels(streams)

        process_streams = []
        for raw_stream in raw_streams:
            process_stream = process_config(raw_stream)
            process_streams.append(process_stream)

        process_streams = group_channels(process_streams)

        all_streams = raw_streams + process_streams

        write_asdf(tfile, all_streams)

        assert is_asdf(tfile)
    except:
        assert 1==2
    finally:
        shutil.rmtree(tdir)


if __name__ == '__main__':
    dummy_test()
