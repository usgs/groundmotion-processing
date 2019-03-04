#!/usr/bin/env python

import os.path
import shutil
import logging
import time

import numpy as np
from gmprocess.io.asdf.core import is_asdf, read_asdf, write_asdf
from gmprocess.io.read import read_data
from gmprocess.processing import process_streams
from gmprocess.config import get_config
from gmprocess.io.test_utils import read_data_dir
import tempfile


def dummy_test():
    # logger = logging.getLogger()
    # logger.setLevel(logging.DEBUG)
    tdir = tempfile.mkdtemp()
    try:
        tfile = os.path.join(tdir, 'test.hdf')

        datafiles, origin = read_data_dir('geonet', 'us1000778i', '*.V1A')

        streams = []
        for netfile in datafiles:
            streams += read_data(netfile)

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

        t1 = time.time()
        processed_streams = process_streams(streams, origin, config=config)
        t2 = time.time()

        dt = t2 - t1

        all_streams = streams + processed_streams

        write_asdf(tfile, all_streams, event=origin)

        assert is_asdf(tfile)

        asdf_streams = read_asdf(tfile)

        # make sure the streams we put in are the same ones we get out
        assert len(asdf_streams) == len(all_streams)

        # # are the raw data the same?
        # raw_input_stream = all_streams[0]
        # input_station = raw_input_stream[0].stats.station
        # for stream in asdf_streams:
        #     stmatch = stream[0].stats.station == input_station
        #     has_prov = len(stream[0].getProvenanceKeys())
        #     if stmatch and not has_prov:
        #         raw_output_stream = stream
        #         break

        # t1 = raw_input_stream[0].max()
        # t2 = raw_output_stream[0].max()
        # np.testing.assert_almost_equal(t1, t2)

        # # are the raw metadata the same?
        # for key, invalue in raw_input_stream[0].stats['standard'].items():
        #     if key not in raw_output_stream[0].stats['standard']:
        #         print('%s missing from output!' % key)
        #         assert 1 == 2
        #     outvalue = raw_output_stream[0].stats['standard'][key]
        #     if isinstance(invalue, float):
        #         np.testing.assert_almost_equal(invalue, outvalue)
        #     else:
        #         print('Comparing values for %s' % key)
        #         assert invalue == outvalue

        # # are the processed data the same?
        # proc_input_stream = all_streams[3]
        # input_station = raw_input_stream[0].stats.station
        # for stream in asdf_streams:
        #     stmatch = stream[0].stats.station == input_station
        #     has_prov = len(stream[0].getProvenanceKeys())
        #     if stmatch and has_prov:
        #         proc_output_stream = stream
        #         break

        # t1 = proc_input_stream[0].max()
        # t2 = proc_output_stream[0].max()
        # np.testing.assert_almost_equal(t1, t2)

        # # are the processed metadata the same?
        # for key, invalue in proc_input_stream[0].stats['standard'].items():
        #     if key not in proc_output_stream[0].stats['standard']:
        #         print('%s missing from output!' % key)
        #         assert 1 == 2
        #     outvalue = proc_output_stream[0].stats['standard'][key]
        #     if isinstance(invalue, float):
        #         np.testing.assert_almost_equal(invalue, outvalue)
        #     else:
        #         assert invalue == outvalue

        # # is the processing history the same?
        # inprov = proc_input_stream[0].getAllProvenance()
        # outprov = proc_output_stream[0].getAllProvenance()
        # if len(inprov) != len(outprov):
        #     assert 1 == 2

        # for i in range(0, len(inprov)):
        #     indict = inprov[i]
        #     outdict = outprov[i]
        #     if indict['prov_id'] != outdict['prov_id']:
        #         assert 1 == 2
        #     inattr = indict['prov_attributes']
        #     outattr = indict['prov_attributes']
        #     for key, invalue in inattr.items():
        #         if key not in outattr:
        #             assert 1 == 2
        #         outvalue = outattr[key]
        #         if isinstance(invalue, float):
        #             np.testing.assert_almost_equal(invalue, outvalue)
        #         else:
        #             assert invalue == outvalue

        # # are the parameters the same?
        # pkeys = proc_input_stream[0].getParameterKeys()
        # for pkey in pkeys:
        #     invalue = proc_input_stream[0].getParameter(pkey)
        #     outvalue = proc_output_stream[0].getParameter(pkey)
        #     assert invalue == outvalue

    except Exception:
        assert 1 == 2
    finally:
        shutil.rmtree(tdir)


if __name__ == '__main__':
    dummy_test()
