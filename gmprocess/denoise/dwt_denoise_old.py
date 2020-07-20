#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ======================================================================
#
#                           Brad T. Aagaard
#                        U.S. Geological Survey
#
# ======================================================================
#

import numpy
import logging

def denoise(stream, wavelet="coif4", remove_bg=True, zero_coarse_levels=1, zero_fine_levels=1, preevent_window=10.0, preevent_threshold_reduction=2.0, store_orig=False, store_noise=False):
    """Remove noise from waveforms using wavelets in a two-step
    process. In the first step, noise is identified via a Kurtosis
    analysis of the wavelet coefficients. In the second step, the
    noise level in a pre-event window is determined for each wavelet
    level and then removed from the waveform using a soft threshold.
    :type wavelet: str
    :param waveform: Name of wavelet to use in denoising.
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
    MODE = "zero"
    
    try:
        import pywt
    except ImportError:
        raise ImportError("_denoise() requires PyWavelets (pywt) Python module.")

    logger = logging.getLogger(__name__)

    dataOut = {}
    if store_orig:
        dataOut["orig"] = stream.copy()

    tracesNoise = []    
    for tr in stream:
        channelLabel = "%s.%s.%s" % (tr.stats.network, tr.stats.station, tr.stats.channel)
        coefsNoise = []

        coefs = pywt.wavedec(tr.data, wavelet, mode=MODE)
        
        if remove_bg:
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
                
                    
        if preevent_window is not None and preevent_window > 0.0:
            numPtsPre = preevent_window*tr.stats.sampling_rate
            nlevels = len(coefs)-1
            for i,coef in enumerate(coefs[1:]):
                level = nlevels - i
                numCoefTarget = int(numPtsPre / 2**level)
                coefPre = coef[:numCoefTarget]
                numCoefPre = coefPre.shape[-1]
                median = numpy.median(numpy.abs(coefPre))
                std = median / 0.6745
                threshold = std * (2.0*numpy.log(numCoefPre)) / preevent_threshold_reduction
                logger.info("Channel %s: Step 2: threshold level: %d, : %f" % (channelLabel, level, threshold,))
                mask = numpy.abs(coef) < threshold
                coefsNoise[1+i][mask] += coef[mask]
                coefsNoise[1+i][~mask] += threshold*numpy.sign(coef[~mask]) # (use for soft mask)
                coef[mask] *= 0.0
                coef[~mask] -= threshold*numpy.sign(coef[~mask]) # (use for soft mask)

        for ilevel in range(1+zero_coarse_levels):
            coefsNoise[ilevel] += coefs[ilevel].copy()
            coefs[ilevel] *= 0.0
        for ilevel in range(zero_fine_levels):
            index = -(1+ilevel)
            coefsNoise[index] += coefs[index].copy()
            coefs[index] *= 0.0
                
        tr.data = pywt.waverec(coefs, wavelet, mode=MODE)

        if store_noise:
            trNoise = tr.copy()
            trNoise.data = pywt.waverec(coefsNoise, wavelet, mode=MODE)
            tracesNoise.append(trNoise)
                
        # Signal to noise ratio
        cArray,cSlices = pywt.coeffs_to_array(coefs)
        cArrayN,cSlices = pywt.coeffs_to_array(coefsNoise)
        # if soft threshold
        mask = numpy.abs(cArray) > 0.0
        rmsSignal = numpy.sqrt(numpy.mean(cArray[mask]**2))
        rmsNoise = numpy.sqrt(numpy.mean(cArrayN[mask]**2))
        # hard threshold
        #rmsSignal = numpy.sqrt(numpy.mean(cArray**2))
        #rmsNoise = numpy.sqrt(numpy.mean(cArrayN**2))
        tr.StoN = rmsSignal/rmsNoise
        logger.info("Channel %s: S/N: %.1f" % (channelLabel, tr.StoN,))

    dataOut["data"] = stream
    if store_noise:
        import obspy.core
        dataOut["noise"] = obspy.core.Stream(traces=tracesNoise)
    
        
    return dataOut