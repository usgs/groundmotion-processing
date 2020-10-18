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

import numpy as np
import logging
import utils

def denoise(st, wavelet="coif4", MODE="zero", remove_bg=True, 
                threshold='soft', zero_coarse_levels=1, zero_fine_levels=1, 
                preevent_window=10.0, preevent_threshold_reduction=2.0, 
                store_orig=False, store_noise=False):
    """Remove noise from waveforms using wavelets in a two-step
    process. In the first step, noise is identified via a Kurtosis
    analysis of the wavelet coefficients. In the second step, the
    noise level in a pre-event window is determined for each wavelet
    level and then removed from the waveform using a soft threshold.

    :type wavelet: str
    :param wavelet: Name of wavelet to use in denoising.
    :type remove_bg: bool
    :param remove_bg: If True, perform the first step in the denoising process.
    :type preevent_window: float
    :param preevent_window: Size of pre-event window to use in second step. Skip second step if <= 0.
    :type preevent_threshold_reduction: float
    :param preevent_threshold_reduction: Factor to reduce threshold of noise level in second step.
    :type store_orig: bool
    :param store_orig: Return a copy of the original waveforms.
    :type store_noise: bool
    :param store_noise: Return the noise waveforms removed.
    :returns: Dictionary containing the denoised waveforms and, if
    requested, original waveforms and noise waveforms.

    """
    # Use of "__name__" is to grab the module's name in this python package namespace
    logger = logging.getLogger(__name__)

    try:
        import pywt
    except ImportError:
        raise ImportError("dwt_denoise() requires PyWavelets (pywt) Python module.")

    # Incorporate use of other wavelets, check that they are valid
    try:
        wt_fams = pywt.families()
        wt_fams_lists = []
        for i, fam in enumerate(wt_fams):
            wt_fams_lists.append(pywt.wavelist(fam))

        if ~(wavelet in wt_fams_lists):
            logger.info("")
    except LookupError:
        logger.info("The wavelet selected by the user is not supported by PyWavelets")

    # Incorporate other options for padding, while default is still zero
        # Do at some point

    # Keep a copy of the input data
    dataOut = {}
    if store_orig:
        dataOut["orig"] = st.copy()

    # Prep in case user wants to also keep noise
    tracesNoise = []
    for tr in st:
        channelLabel = "%s.%s.%s" % (tr.stats.network,
                                     tr.stats.station,
                                     tr.stats.channel)
        coefsNoise = []

        coefs = pywt.wavedec(tr.data, wavelet, mode=MODE)

        # Do kurtosis analysis to determine noise
        if remove_bg:
            coefsNoise = utils.kurtosis(channelLabel, coefs, logger)

        # Identify pre-event noise at all wavelet levels and remove
        coefs, coefsNoise = utils.remove_pre_event_noise(tr,coefs, preevent_window, preevent_threshold_reduction)
        for ilevel in range(1+zero_coarse_levels):
            coefsNoise[ilevel] += coefs[ilevel].copy()
            coefs[ilevel] *= 0.0
        for ilevel in range(zero_fine_levels):
            index = -(1+ilevel)
            coefsNoise[index] += coefs[index].copy()
            coefs[index] *= 0.0

        # Reconstruct a reduced noise signal from processed wavelet coefficients
        tr.data = pywt.waverec(coefs, wavelet, mode=MODE)

        if store_noise:
            trNoise = tr.copy()
            trNoise.data = pywt.waverec(coefsNoise, wavelet, mode=MODE)
            tracesNoise.append(trNoise)
                
        #Signal to noise ratio
        if threshold == 'soft':
            tr = utils.soft_threshold(tr, channelLabel, coefs, coefsNoise, logger)
        elif threshold == 'hard':
            tr = utils.soft_threshold(tr, channelLabel, coefs, coefsNoise, logger)
        elif threshold == 'block':
            logger.info("Block thresholding currenlty under development")
        else:
            logger.info("Unsupported thresholding option")

    dataOut["data"] = st
    if store_noise:
        import obspy.core
        dataOut["noise"] = obspy.core.Stream(traces=tracesNoise)
        
    return dataOut


def denoise_trace(tr, wavelet="coif4", MODE="zero", remove_bg=True,
                      threshold='soft', zero_coarse_levels=1,
                      zero_fine_levels=1, preevent_window=10.0,
                      preevent_threshold_reduction=2.0, store_orig=False,
                      store_noise=False):

    """Remove noise from a single trace waveform using wavelets in
    a two-step process. In the first step, noise is identified via a
    Kurtosis analysis of the wavelet coefficients. In the second step, the
    noise level in a pre-event window is determined for each wavelet
    level and then removed from the waveform using a soft threshold.

    :type wavelet: str
    :param wavelet: Name of wavelet to use in denoising.
    :type remove_bg: bool
    :param remove_bg: If True, perform the first step in the denoising process.
    :type preevent_window: float
    :param preevent_window: Size of pre-event window to use in second step. Skip second step if <= 0.
    :type preevent_threshold_reduction: float
    :param preevent_threshold_reduction: Factor to reduce threshold of noise level in second step.
    :type store_orig: bool
    :param store_orig: Return a copy of the original waveforms.
    :type store_noise: bool
    :param store_noise: Return the noise waveforms removed.
    :returns: Dictionary containing the denoised waveforms and, if
    requested, original waveforms and noise waveforms.

    """
    # Use of "__name__" is to grab the module's name in this python package namespace
    logger = logging.getLogger(__name__)

    try:
        import pywt
    except ImportError:
        raise ImportError("dwt_denoise() requires PyWavelets (pywt) Python module.")

    # Incorporate options for other wavelets, check that they are valid
    try:
        wt_fams = pywt.families()
        wt_fams_lists = []
        for i, fam in enumerate(wt_fams):
            wt_fams_lists.append(pywt.wavelist(fam))

        if ~(wavelet in wt_fams_lists):
            logger.info("")
    except LookupError:
        logger.info("The wavelet selected by the user is not supported by PyWavelets")

    # Incorporate other options for padding, while default is still zero

    # Keep a copy of the input data
    dataOut = {}
    if store_orig:
        dataOut["orig"] = tr.copy()

    # Prep in case user wants to also keep the "noise"
    tracesNoise = []
    channelLabel = utils.get_channel_label(tr)
    coefsNoise = []
    coefs = pywt.wavedec(tr.data, wavelet, mode=MODE)

    # Do kurtosis analysis to determine noise
    if remove_bg:
        coefsNoise = utils.kurtosis(channelLabel, coefs, logger)

    # Identify pre-event noise at all wavelet levels and remove
    coefs, coefsNoise = utils.remove_pre_event_noise(tr, coefs, preevent_window, preevent_threshold_reduction)
    for ilevel in range(1+zero_coarse_levels):
        coefsNoise[ilevel] += coefs[ilevel].copy()
        coefs[ilevel] *= 0.0
    for ilevel in range(zero_fine_levels):
        index = -(1+ilevel)
        coefsNoise[index] += coefs[index].copy()
        coefs[index] *= 0.0

    # Reconstruct a reduced noise signal from processed wavelet coefficients
    tr.data = pywt.waverec(coefs, wavelet, mode=MODE)

    # Store a copy of the noise
    if store_noise:
        trNoise = tr.copy()
        trNoise.data = pywt.waverec(coefsNoise, wavelet, mode=MODE)
        tracesNoise.append(trNoise)

    # Signal to noise ratio
    if threshold == 'soft':
        tr = utils.soft_threshold(tr, channelLabel, coefs, coefsNoise, logger)
    elif threshold == 'hard':
        tr = utils.hard_threshold(tr, channelLabel, coefs, coefsNoise, logger)
    elif threshold == 'block':
        logger.info("Block thresholding currenlty under development")
    else:
        logger.info("Unsupported thresholding option")

    dataOut["data"] = tr
    if store_noise:
        import obspy.core
        dataOut["noise"] = obspy.core.Stream(traces=tracesNoise)

    return dataOut
