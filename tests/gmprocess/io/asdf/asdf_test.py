#!/usr/bin/env python

import os.path
import glob
import shutil
import logging

import numpy as np
from gmprocess.io.asdf.core import is_asdf, read_asdf, write_asdf
from gmprocess.io.asdf.asdf_utils import (inventory_from_stream,
                                          get_event_info, get_event_dict)
from gmprocess.io.read import read_data
from gmprocess.stream import group_channels
from gmprocess.processing import process_streams
from gmprocess.config import get_config
from gmprocess.io.asdf.provenance import ACTIVITIES
import tempfile


def dummy_test():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # where is this script?
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, '..', '..', '..', 'data', 'asdf')
    netdir = os.path.join(homedir, '..', '..', '..', 'data', 'geonet')
    tdir = tempfile.mkdtemp()
    eventid = 'us2000cnnl'
    eventid = 'us1000778i'  # M7.8 NZ Nov 2016
    try:
        tfile = os.path.join(tdir, 'test.hdf')

        streams = []
        # netfiles = glob.glob(os.path.join(netdir, 'AOM0011801241951*'))
        # for netfile in netfiles:
        #     stream = read_data(netfile)
        #     streams.append(stream)

        # streams = group_channels(streams)

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

        # corner frequency checks may drop data that we want to use
        # so switch to constant values
        config['corner_frequencies']['method'] = 'constant'

        origin = get_event_dict(eventid)

        processed_streams = process_streams(streams, origin, config=config)

        all_streams = streams + processed_streams

        write_asdf(tfile, all_streams, event=origin)

        assert is_asdf(tfile)

        asdf_streams = read_asdf(tfile)

        # make sure the streams we put in are the same ones we get out
        assert len(asdf_streams) == len(all_streams)

        # are the raw data the same?
        raw_input_stream = all_streams[0]
        raw_output_stream = asdf_streams[0]

        t1 = raw_input_stream[0].max()
        t2 = raw_output_stream[0].max()
        np.testing.assert_almost_equal(t1, t2)

        # are the raw metadata the same?
        for key, invalue in raw_input_stream[0].stats['standard'].items():
            if key not in raw_output_stream[0].stats['standard']:
                print('%s missing from output!' % key)
                assert 1 == 2
            outvalue = raw_output_stream[0].stats['standard'][key]
            if isinstance(invalue, float):
                np.testing.assert_almost_equal(invalue, outvalue)
            else:
                assert invalue == outvalue

        # are the processed data the same?
        proc_input_stream = all_streams[1]
        proc_output_stream = asdf_streams[1]
        t1 = proc_input_stream[0].max()
        t2 = proc_output_stream[0].max()
        np.testing.assert_almost_equal(t1, t2)

        # are the processed metadata the same?
        for key, invalue in proc_input_stream[0].stats['standard'].items():
            if key not in proc_output_stream[0].stats['standard']:
                print('%s missing from output!' % key)
                assert 1 == 2
            outvalue = proc_output_stream[0].stats['standard'][key]
            if isinstance(invalue, float):
                np.testing.assert_almost_equal(invalue, outvalue)
            else:
                assert invalue == outvalue

        # is the processing history the same?
        inproc_history = proc_input_stream[0].stats['processing_parameters']
        outproc_history = proc_output_stream[0].stats['processing_parameters']
        new_inproc_history = []
        for pdict in inproc_history:
            if pdict['prov_id'] in ACTIVITIES:
                new_inproc_history.append(pdict)
        for idx in range(0, len(new_inproc_history)):
            inprovdict = new_inproc_history[idx]
            outprovdict = outproc_history[idx]
            inprov_id = inprovdict['prov_id']
            outprov_id = outprovdict['prov_id']
            if inprov_id != outprov_id:
                print('%s missing from output!' % key)
                assert 1 == 2

            in_attr = inprovdict['prov_attributes']
            out_attr = outprovdict['prov_attributes']

            for key, invalue in in_attr.items():
                outvalue = out_attr[key]
            if isinstance(invalue, float):
                np.testing.assert_almost_equal(invalue, outvalue)
            else:
                assert invalue == outvalue
    except:
        assert 1 == 2
    finally:
        shutil.rmtree(tdir)


if __name__ == '__main__':
    dummy_test()
