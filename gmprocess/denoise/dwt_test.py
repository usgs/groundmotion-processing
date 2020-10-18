# -*- coding: utf-8 -*-
#
# ======================================================================
#
#                           Gabriel Ferragut
#              U.S. Geological Survey/ University of Oregon
#
# ======================================================================
#

# stdlib imports
import os
import math
import logging

# third party imports
import numpy as np
import obspy
import pkg_resources

# local imports
from gmprocess.denoise import dwt
from gmprocess.denoise import utils

from gmprocess.io.read_directory import directory_to_streams
from gmprocess.io.test_utils import read_data_dir
from gmprocess.io.read import read_data
from gmprocess.logging import setup_logger
from gmprocess.streamcollection import StreamCollection

setup_logger()
#%% Examples of grabbing some test data

# # read usc data
# dpath = os.path.join('data', 'testdata', 'usc', 'ci3144585')
# directory = pkg_resources.resource_filename('gmprocess', dpath)
# usc_streams, unprocessed_files, unprocessed_file_errors = \
#     directory_to_streams(directory)
# assert len(usc_streams) == 7

# usc_sc = StreamCollection(usc_streams)

# # read dmg data
# dpath = os.path.join('data', 'testdata', 'dmg', 'ci3144585')
# directory = pkg_resources.resource_filename('gmprocess', dpath)
# dmg_streams, unprocessed_files, unprocessed_file_errors = \
#     directory_to_streams(directory)
# assert len(dmg_streams) == 1

# dmg_sc = StreamCollection(dmg_streams)

def test_dwt_denoise():
    """ Check that sample data fed into dwt_denoise() can be processed and
    that the returned signal is reasonable"""

    # Loma Prieta test station (nc216859)
    data_files, origin = read_data_dir('geonet', 'us1000778i', '*.V1A')
    streams = []
    for f in data_files:
        streams += read_data(f)

    # Perhaps too general


def test_dwt_denoise_trace():
    """ Check that sample data fed into dwt_denoise_trace() can be processed
    and that the returned signal is reasonable (for just one trace)"""

    # Loma Prieta test station (nc216859)
    data_files, origin = read_data_dir('geonet', 'us1000778i', '*.V1A')
    trace = []
    trace = read_data(data_files[0])

    dataOut = dwt.denoise_trace(tr=trace)

    # Look at frequency content? Samples?

    return dataOut


def test_kurtosis():
    """ A measure of the kurtosis should indicate to what degree the tails
    of a distribution deviate from a standard normal distribution"""
    return

    # Perhaps test agains a perfectly normal distribution?
    # here kurtosis should be zero

    # Maybe make a synthetic signal with pre-defined frequency content and
    # zero noise to check kurtosis?


def test_keep_original_data():
    """ Run dwt_denoise() with the keep original data option,
    assert copy of original data exists"""

    # Loma Prieta test station (nc216859)
    data_files, origin = read_data_dir('geonet', 'us1000778i', '*.V1A')
    streams = []
    for f in data_files:
        streams += read_data(f)

    dataOut = dwt.denoise(st=streams,store_orig=True)

    """ Assert a variable exists? Try catch clause to see if it exist?"""
    # assert dataOut["orig"] != null

def test_keep_noise():
    """ Run dwt_denoise() with the keep noise option,
    assert copy of noise exists"""

    # Make sure it's nonzero, and probably below some "reasonable" level.
    # Certainly below the amplitude of the original signal

    # Loma Prieta test station (nc216859)
    data_files, origin = read_data_dir('geonet', 'us1000778i', '*.V1A')
    streams = []
    for f in data_files:
        streams += read_data(f)

    dataOut = dwt.denoise(st=streams,store_noise=True)

    """ Assert a variable exists? Try catch clause to see if it exist?"""
    # assert dataOut["orig"] != null


def test_signal_reconstruction():
    return

    # Check that a time series is correctly reconstructed, has amplitude
    # that is lower than original signal, etc


def test_soft_threshold():
    # Need to check coefficients to see if soft thresholding working
    return


def test_hard_threshold():
    # Need to check coefficients to see if soft thresholding working
    return


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    # test_plot()
    test_dwt_denoise()
    # test_kurtosis()
    # test_keep_original_data()
    # test_keep_noise()
    # test_signal_reconstruction()
    # test_soft_threshold()
    # test_hard_threshold()
