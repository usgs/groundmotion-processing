# -*- coding: utf-8 -*-
#
# ======================================================================
#
#                           Brad T. Aagaard
#                        U.S. Geological Survey
#
#               Modified for gmprocess by Gabriel Ferragut
#              U.S. Geological Survey/ University of Oregon
#
# ======================================================================
#

# stdlib imports
import os
import logging

# local imports
from gmprocess.denoise import dwt
from gmprocess import filtering
from gmprocess.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.processing import process_streams
from gmprocess.logging import setup_logger
from gmprocess.io.test_utils import read_data_dir

# third party imports
import pywt
import numpy as np
import matplotlib as plt

setup_logger()
# %% Plotting and method checks


def add_random_noise(st, sigma=0.1):
    """
    Takes randomly generated Gaussian noise and applies it to the input signal

    Args
        st (StationStream):
            Stream of data

        sigma (float):
            Parameter controlling the "spread" of the Gaussian noise

    Returns:
        noisy_signal (StationStream):
            A modified stream with random Gaussian noise added

    """
    noise = np.zeros(len(st))
    noisy_signal = np.zeros(len(st))

    for i in range(len(st)):

        noise[i] = np.random.normal(noise[i], sigma, 1)

        noisy_signal[i] = st[i] + noise[i]

    return noisy_signal

def add_bandpassed_random_noise(st, sigma=0.1,
                                min_freq=0.0, max_freq=40.0,
                                samples=1024, sampling_rate=1):
    """
    Filters random Gaussian noise to produce band limited noise
    and applies it to the input signal

    Args
        st (StationStream):
            Stream of data
        sigma (float):
            Parameter controlling the "spread" of the Gaussian noise



    Returns:
        noisy_signal (StationStream):
            A modified stream with random Gaussian noise added

    """

    noisy_signal = st

    return noisy_signal


def wavelet_bandpass_comparison(st, residual=True, overlay=True):
    """
    Performs denoising on traces in stream with two methods using their
    default values and compares results graphically
    """

    wavelet_denoised = dwt.denoise(st)

    highpass_denoised = filtering.highpass_filter(st)
    bandpass_denoised = filtering.lowpass_filter(highpass_denoised)

    fig1 = plt.figure()
    plt.plot(wavelet_denoised)

    fig2 = plt.figure()
    plt.plot(bandpass_denoised)

    return fig1, fig2

# def wavelet_bandpass_comparison_trace(tr, residual=True, overlay=True):
#     """
#     Performs denoising on a single trace with two methods and compares
#     results graphically
#     """
#     return

# %% Formatting


def get_channel_label(tr):
    """ """
    channel_label = "%s.%s.%s" % (tr.stats.network,
                                  tr.stats.station,
                                  tr.stats.channel)

    logging.info("channelLabel is " + channel_label)

    return channel_label

# %% Kurtosis analysis of noise


def kurtosis(channelLabel, coefs, logger):
    """ """
    logger = logging.getLogger(__name__)
    coefsNoise = []

    for coef in coefs:
        numCoef = coef.shape[-1]
        std = np.std(coef)
        mean = np.mean(coef)
        kurt = np.sum((coef-mean)**4) / (numCoef*std**4) - 3
        threshold = (24.0 / (numCoef*(1.0-0.9)))**0.5

        logger.info("Channel %s: Step 1, kurt: %f, threshold: %f" % (channelLabel, kurt, threshold,))
        mask = np.abs(kurt) <= threshold
        if mask:
            coefsNoise.append(coef.copy())
            coef *= 0.0
        else:
            coefsNoise.append(0.0*coef)

    return coefsNoise

# %% Pre-event window noise


def remove_pre_event_noise(tr, coefs, preevent_window,
                           preevent_threshold_reduction):
    """ """
    logger = logging.getLogger(__name__)

    coefsNoise = []
    channel_label = get_channel_label(tr)

    if preevent_window is not None and preevent_window > 0.0:
        numPtsPre = preevent_window*tr.stats.sampling_rate
        nlevels = len(coefs)-1

        for i, coef in enumerate(coefs[1:]):
            level = nlevels - i
            numCoefTarget = int(numPtsPre / 2**level)
            coefPre = coef[:numCoefTarget]
            numCoefPre = coefPre.shape[-1]
            median = np.median(np.abs(coefPre))
            std = median / 0.6745
            threshold = std * (2.0*np.log(numCoefPre)) / preevent_threshold_reduction
            logger.info("Channel %s: Step 2: threshold level: %d, : %f"% (channel_label, level, threshold,))
            mask = np.abs(coef) < threshold
            coefsNoise[1+i][mask] += coef[mask]
            coefsNoise[1+i][~mask] += threshold*np.sign(coef[~mask])
            coef[mask] *= 0.0
            coef[~mask] -= threshold*np.sign(coef[~mask])

    return coefs, coefsNoise

#%% Thresholding


def soft_threshold(tr, coefs, coefsNoise):
    """ """

    logger = logging.getLogger(__name__)
    channel_label = get_channel_label(tr)

    cArray, cSlices = pywt.coeffs_to_array(coefs)
    cArrayN, cSlicesN = pywt.coeffs_to_array(coefsNoise)

    mask = np.abs(cArray) > 0.0
    rmsSignal = np.sqrt(np.mean(cArray[mask]**2))
    rmsNoise = np.sqrt(np.mean(cArrayN[mask]**2))

    tr.StoN = rmsSignal/rmsNoise
    logger.info("Channel %s: S/N: %.1f" % (channel_label, tr.StoN,))

    return tr


def hard_threshold(tr, chan, coefs, coefsNoise):
    """ """

    logger = logging.getLogger(__name__)

    cArray, cSlices = pywt.coeffs_to_array(coefs)
    cArrayN, cSlicesN = pywt.coeffs_to_array(coefsNoise)

    rmsSignal = np.sqrt(np.mean(cArray**2))
    rmsNoise = np.sqrt(np.mean(cArrayN**2))

    tr.StoN = rmsSignal/rmsNoise
    logger.info("Channel %s: S/N: %.1f" % (chan, tr.StoN,))

    return tr


def block_threshold(coefs, coefsNoise):
    """ """

    logger = logging.getLogger(__name__)
    logger.info("Block thresholding currenlty under development")

    return
