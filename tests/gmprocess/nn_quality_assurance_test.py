#!/usr/bin/env python

# stdlib imports
import os
import logging

# third party imports
import numpy as np
import pkg_resources

# local imports
from gmprocess.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.processing import process_streams
from gmprocess.logging import setup_logger
from gmprocess.io.test_utils import read_data_dir
from gmprocess.config import get_config, update_dict

# homedir = os.path.dirname(os.path.abspath(__file__))
# datadir = os.path.join(homedir, '..', 'data', 'testdata')

datapath = os.path.join('data', 'testdata')
datadir = pkg_resources.resource_filename('gmprocess', datapath)

setup_logger()


def test_nnet():

    conf = get_config()

    update = {
        'processing': [
            {'check_free_field': {'reject_non_free_field': True}},
            {'check_max_amplitude': {'max': '2e6', 'min': 5}},
            {'max_traces': {'n_max': 3}},
            {'detrend': {'detrending_method': 'demean'}},
            #            {'check_zero_crossings': {'min_crossings': 10}},
            {'detrend': {'detrending_method': 'linear'}},
            {'detrend': {'detrending_method': 'demean'}},
            {'compute_snr': {'bandwidth': 20.0,
                             'check': {'max_freq': 5.0,
                                       'min_freq': 0.2,
                                       'threshold': 3.0}}},
            {'NNet_QA': {'acceptance_threshold': 0.5,
                         'model_name': 'CantWell'}}
        ]
    }
    update_dict(conf, update)

    data_files, origin = read_data_dir('geonet', 'us1000778i', '*.V1A')
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)
    test = process_streams(sc, origin)
    nnet_dict = test[0].getStreamParam('nnet_qa')
    np.testing.assert_allclose(
        nnet_dict['score_HQ'], 0.99319980988565215, rtol=1e-5)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_nnet()
