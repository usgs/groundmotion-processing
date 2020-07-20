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

import pywt
import numpy
import logging

# local imports
from gmprocess.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.processing import process_streams
from gmprocess.logging import setup_logger
from gmprocess.io.test_utils import read_data_dir

#%% Formatting


def get_channel_label(tr):
    """ """
    logger = logging.getLogger(__name__)
    channelLabel = "%s.%s.%s" % (tr.stats.network, tr.stats.station, tr.stats.channel)

    return channelLabel

#%% Kurtosis analysis of noise


def kurtosis(channelLabel, coefs, logger):
    """ """
    logger = logging.getLogger(__name__)
    coefsNoise = []

    for coef in coefs:
        numCoef = coef.shape[-1]
        std = numpy.std(coef)
        mean = numpy.mean(coef)
        kurt = numpy.sum((coef-mean)**4) / (numCoef*std**4) - 3
        threshold = (24.0 / (numCoef*(1.0-0.9)))**0.5

        logger.info("Channel %s: Step 1, kurt: %f, threshold: %f" % (channelLabel, kurt, threshold,))
        mask = numpy.abs(kurt) <= threshold
        if mask:
            coefsNoise.append(coef.copy())
            coef *= 0.0
        else:
            coefsNoise.append(0.0*coef)

    return coefsNoise

#%% Pre-event window noise


def remove_pre_event_noise(tr, coefs, preevent_window, preevent_threshold_reduction):
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
            median = numpy.median(numpy.abs(coefPre))
            std = median / 0.6745
            threshold = std * (2.0*numpy.log(numCoefPre)) / preevent_threshold_reduction
            logger.info("Channel %s: Step 2: threshold level: %d, : %f" % (channel_label, level, threshold,))
            mask = numpy.abs(coef) < threshold
            coefsNoise[1+i][mask] += coef[mask]
            coefsNoise[1+i][~mask] += threshold*numpy.sign(coef[~mask]) # (use for soft mask)
            coef[mask] *= 0.0
            coef[~mask] -= threshold*numpy.sign(coef[~mask]) # (use for soft mask)

    return coefs, coefsNoise

#%% Thresholding


def soft_threshold(tr, coefs, coefsNoise):
    """ """

    logger = logging.getLogger(__name__)
    channel_label = get_channel_label(tr)

    cArray, cSlices = pywt.coeffs_to_array(coefs)
    cArrayN, cSlicesN = pywt.coeffs_to_array(coefsNoise)

    mask = numpy.abs(cArray) > 0.0
    rmsSignal = numpy.sqrt(numpy.mean(cArray[mask]**2))
    rmsNoise = numpy.sqrt(numpy.mean(cArrayN[mask]**2))

    tr.StoN = rmsSignal/rmsNoise
    logger.info("Channel %s: S/N: %.1f" % (channel_label, tr.StoN,))

    return tr


def hard_threshold(tr, chan, coefs, coefsNoise):
    """ """

    logger = logging.getLogger(__name__)

    cArray, cSlices = pywt.coeffs_to_array(coefs)
    cArrayN, cSlicesN = pywt.coeffs_to_array(coefsNoise)

    rmsSignal = numpy.sqrt(numpy.mean(cArray**2))
    rmsNoise = numpy.sqrt(numpy.mean(cArrayN**2))

    tr.StoN = rmsSignal/rmsNoise
    logger.info("Channel %s: S/N: %.1f" % (chan, tr.StoN,))

    return tr


def block_threshold(coefs, coefsNoise):
    """ """

    logger = logging.getLogger(__name__)
    logger.info("Block thresholding currenlty under development")

    return
