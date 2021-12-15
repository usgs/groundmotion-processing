#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import logging
from scipy import signal
from scipy.integrate import cumtrapz
from gmprocess.utils.config import get_config
from gmprocess.waveform_processing.filtering import \
    lowpass_filter_trace, highpass_filter_trace


def PolynomialFit_SJB(st, target = 0.02, tol = 0.001,
                           maxiter = 30, maxfc = 0.5):
    """Search for highpass corner using Ridder's method such that
        it satisfies the criterion that the ratio between the maximum of a third order polynomial
        fit to the displacement time series and the maximum of the displacement
        timeseries is a target % within a tolerance.

    This algorithm searches between an initial corner frequency that was selected
    as configured in the `get_corner_frequencies` step and a maximum fc.
    
    Method developed originally by Scott Brandenberg

    Args:
        st (StationStream):
            Stream of data.
        target (float):
            target percentage for ratio between max polynomial value and max displacement.
        tol (float):
            tolereance for matching the ratio target
        maxiter (float):
            maximum number of allowed iterations in Ridder's method
        maxfc (float):
            Maximum allowable value of the highpass corner freq.

    Returns:
        StationStream.

    """

    for tr in st:
        if not tr.hasParameter('corner_frequencies'):
            tr.fail("Cannot apply PolynomialFit_SJB method because "
                    "initial corner frequencies are not set.")
        else:
            initial_corners = tr.getParameter('corner_frequencies')
            f_hp = 0.0001 #GP: Want the initial bounds to encompass the solution
            
            out = __ridder_log(tr,f_hp,
                       target, tol,
                       maxiter, maxfc)

            if out[0] == True:
                    initial_corners['highpass'] = out[1]
                    tr.setParameter('corner_frequencies', initial_corners)
                    logging.debug("Ridder fchp passed to trace stats = %s with misfit %s", out[1],out[2])

            else:
                 tr.fail("Initial Ridder residuals were both positive, cannot find appropriate fchp below maxfc")
               
    return st

def __ridder_log(tr,f_hp,
               target = 0.02, tol = 0.001,
               maxiter = 30, maxfc = 0.5):
    logging.debug("Ridder activated")
    output = {}
    acc = tr.copy()
    acc.detrend("demean")
    
    # apply window
    #  window = signal.tukey(len(acc), alpha=0.2) #GP: use Hann taper to be consistent
    acc = acc.taper(max_percentage=0.05,type = "hann",side = "both") #GP: taper is applied to the signal window before this step
    # acc.data = acc.data * window
    
    time = np.linspace(0, acc.stats.delta * len(acc), len(acc))
    Facc = np.fft.rfft(acc, n = len(acc))
    freq = np.fft.rfftfreq(len(acc), acc.stats.delta)
    fc0 = f_hp
    Facc0 = Facc
    #disp0 = get_disp(freq,Facc,len(acc))
    disp0 = get_disp_timedomain(Facc,acc.stats.delta,len(acc))
    R0 = get_residual(time, disp0, target)
    
    fc2 = maxfc
    Facc2 = filtered_Facc(Facc, freq, fc2, order = 5)
    #disp2 = get_disp(freq,Facc2,len(acc))
    disp2 = get_disp_timedomain(Facc2,acc.stats.delta,len(acc))

    R2 = get_residual(time, disp2, target)
    if ((np.sign(R0) < 0) and (np.sign(R2) < 0)):
                    #output = {'status': True, 'fc (Hz)': fc0, 'acc (g)': np.fft.irfft(Facc0), 'vel (m/s)': get_vel(freq, Facc0), 'disp (m)': get_disp(freq, Facc0)}
       output = [True, fc0, np.abs(R0)]
       return (output)
    if ((np.sign(R0) > 0) and (np.sign(R2) > 0)):
        output = [False]
        return (output)
                    
    for i in range(maxiter):
        logging.debug("Ridder iteration = %s" % i)
        fc1 = np.exp(0.5 * (np.log(fc0) + np.log(fc2)))
        Facc1 = filtered_Facc(Facc, freq, fc1, order = 5)
        #disp = get_disp(freq,Facc1,len(acc))
        disp = get_disp_timedomain(Facc1,acc.stats.delta,len(acc))
        R1 = get_residual(time, disp, target)
        fc3 = np.exp(np.log(fc1) + (np.log(fc1) - np.log(fc0)) * np.sign(R0) * R1 / (np.sqrt(R1 ** 2 - R0 * R2)))
        fc3 = np.min([maxfc, fc3])
        Facc3 = filtered_Facc(Facc, freq, fc3, order = 5)
        #disp = get_disp(freq,Facc3,len(acc))
        disp = get_disp_timedomain(Facc3, acc.stats.delta,len(acc))
        R3 = get_residual(time, disp, target)
        if ((np.abs(R3) <= tol) or (i == maxiter - 1)):
            output = [True, fc3, np.abs(R3)]
            break
        if (R1 * R3 < 0):
            fc0 = fc1
            fc2 = fc3
            R0 = R1
            R2 = R3
        elif (np.sign(R2) != np.sign(R3)):
            fc0 = fc2
            fc2 = fc3
            R0 = R2
            R2 = R3
        else:
            fc0 = fc0
            fc2 = fc3
            R0 = R0
            R2 = R3
    return (output)

def MAX(vx):
    return np.max([np.max(vx), -np.min(vx)])

def filtered_Facc(Facc, freq, fc, order):
    filtered_Facc = []
    for Fa, f in zip(Facc, freq):
        if (f == 0):
            filtered_Facc.append(0.0)
        else:
            filtered_Facc.append(Fa / (np.sqrt(1.0 + (fc / f) ** (2.0 * order))))
    return filtered_Facc

def get_disp(freq, Facc,N):
    Fdisp = []
    for facc, f in zip(Facc, freq):
        if (f == 0):
            Fdisp.append(0.0)
        else:
            Fdisp.append((facc/100)/ (2.0j * np.pi * f) ** 2) #convert from cm/s^2 to m/s^2
    disp = np.fft.irfft(Fdisp,n=N)*100
    return(disp)

def get_disp_timedomain(Facc,delta,N):
    acc_time = np.fft.irfft(Facc,n=N)
    disp = cumtrapz(cumtrapz(acc_time, dx=delta, initial=0),
                         dx=delta, initial=0)
    return(disp)

def get_residual(time, disp, target):
    coef = np.polyfit(time[0:len(disp)], disp, 6)
    fit = []
    for t in time:
        fit.append(np.polyval(coef, t))
    return (MAX(fit) / MAX(disp) - target)

