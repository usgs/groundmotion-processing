#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import os

# third party imports
import numpy as np
import pkg_resources

# local imports
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.utils.logging import setup_logger
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.config import get_config, update_dict

datapath = os.path.join('data', 'testdata')
datadir = pkg_resources.resource_filename('gmprocess', datapath)

setup_logger()


def test_nnet():

    conf = get_config()

    update = {
        'processing': [{
            'detrend': {'detrending_method': 'demean'}
        }, {
            'detrend': {'detrending_method': 'linear'}
        }, {
            'compute_snr': {
                'bandwidth': 20.0,
                'check': {
                    'max_freq': 5.0,
                    'min_freq': 0.2,
                    'threshold': 3.0}
            }
        }, {
            'NNet_QA': {
                'acceptance_threshold': 0.5,
                'model_name': 'CantWell'
            }
        }]
    }
    update_dict(conf, update)

    data_files, origin = read_data_dir('geonet', 'us1000778i', '*.V1A')
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)
    test = process_streams(sc, origin, conf)
    tstream = test.select(station='HSES')[0]
    nnet_dict = tstream.getStreamParam('nnet_qa')
    np.testing.assert_allclose(
        nnet_dict['score_HQ'], 0.99321798811740059, rtol=1e-3)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_nnet()
