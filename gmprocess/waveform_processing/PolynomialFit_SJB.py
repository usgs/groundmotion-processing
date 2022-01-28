#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import logging
from gmprocess.utils.config import get_config
from gmprocess.waveform_processing.integrate import get_disp
from scipy import signal


def PolynomialFit_SJB(
    st, target=0.02, tol=0.001, polynomial_order=6.0, maxiter=30, maxfc=0.5, config=None
):
    """Search for highpass corner using Ridder's method.

    Search such that the criterion that the ratio between the maximum of a third order
    polynomial fit to the displacement time series and the maximum of the displacement
    timeseries is a target % within a tolerance.

    This algorithm searches between a low initial corner frequency a maximum fc.

    Method developed originally by Scott Brandenberg

    Args:
        st (StationStream):
            Stream of data.
        target (float):
            target percentage for ratio between max polynomial value and max
            displacement.
        tol (float):
            tolereance for matching the ratio target
        polynomial_order (float):
            order of polynomial to fit to displacement time series.
        maxiter (float):
            maximum number of allowed iterations in Ridder's method
        maxfc (float):
            Maximum allowable value of the highpass corner freq.
        int_method (string):
            method used to perform integration between acceleration, velocity, and
            dispacement. Options are "frequency_domain", "time_domain_zero_init" or
            "time_domain_zero_mean"
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream.

    """
    if config is None:
        config = get_config()

    for tr in st:
        if not tr.hasParameter("corner_frequencies"):
            tr.fail(
                "Have not applied PolynomialFit_SJB method because "
                "initial corner frequencies are not set."
            )
        else:
            initial_corners = tr.getParameter("corner_frequencies")
            f_hp = 0.0001

            out = __ridder_log(
                tr, f_hp, target, tol, polynomial_order, maxiter, maxfc, config
            )

            if out[0] == True:
                if out[1] <= initial_corners["highpass"]:
                    logging.debug(
                        "Polyfit returns value less than SNR fchp. Adopting SNR fchp"
                    )
                else:
                    tr.setParameter(
                        "corner_frequencies",
                        {
                            "type": "snr_polyfit",
                            "highpass": out[1],
                            "lowpass": initial_corners["lowpass"],
                        },
                    )
                    logging.debug(
                        "Ridder fchp passed to trace stats = %s with misfit %s",
                        out[1],
                        out[2],
                    )

            else:
                tr.fail(
                    "Initial Ridder residuals were both positive, cannot find "
                    "appropriate fchp below maxfc."
                )

    return st


def __ridder_log(
    tr,
    f_hp,
    target=0.02,
    tol=0.001,
    polynomial_order=6,
    maxiter=30,
    maxfc=0.5,
    config=None,
):

    if config is None:
        config = get_config()

    int_config = config["integration"]

    logging.debug("Ridder activated")
    output = {}
    acc = tr.copy()
    acc.detrend("demean")

    # apply Tukey window
    window = signal.tukey(len(acc.data), alpha=0.2)
    acc.data = window * acc.data

    time = np.linspace(0, acc.stats.delta * len(acc), len(acc))
    Facc = np.fft.rfft(acc, n=len(acc))
    freq = np.fft.rfftfreq(len(acc), acc.stats.delta)
    fc0 = f_hp
    disp0 = get_disp(acc, config=config)
    R0 = get_residual(time, disp0, target, polynomial_order)

    fc2 = maxfc
    Facc2 = filtered_Facc(Facc, freq, fc2, order=5)
    acc2 = tr.copy()
    acc2.data = np.fft.irfft(Facc2, len(acc))
    disp2 = get_disp(acc2, config=config)

    R2 = get_residual(time, disp2, target, polynomial_order)
    if (np.sign(R0) < 0) and (np.sign(R2) < 0):
        output = [True, fc0, np.abs(R0)]
        return output

    if (np.sign(R0) > 0) and (np.sign(R2) > 0):
        output = [False]
        return output

    for i in np.arange(maxiter):
        logging.debug("Ridder iteration = %s" % i)
        fc1 = np.exp(0.5 * (np.log(fc0) + np.log(fc2)))
        Facc1 = filtered_Facc(Facc, freq, fc1, order=5)
        acc1 = acc.copy()
        acc1.data = np.fft.irfft(Facc1, len(acc))
        disp = get_disp(acc1, config=config)
        R1 = get_residual(time, disp, target, polynomial_order)
        fc3 = np.exp(
            np.log(fc1)
            + (np.log(fc1) - np.log(fc0))
            * np.sign(R0)
            * R1
            / (np.sqrt(R1 ** 2 - R0 * R2))
        )
        fc3 = np.min([maxfc, fc3])
        Facc3 = filtered_Facc(Facc, freq, fc3, order=5)
        acc3 = acc.copy()
        acc3.data = np.fft.irfft(Facc3, len(acc))
        disp = get_disp(acc3, config=config)
        R3 = get_residual(time, disp, target, polynomial_order)
        if (np.abs(R3) <= tol) or (i == maxiter - 1):
            output = [True, fc3, np.abs(R3)]
            break
        if R1 * R3 < 0:
            fc0 = fc1
            fc2 = fc3
            R0 = R1
            R2 = R3
        elif np.sign(R2) != np.sign(R3):
            fc0 = fc2
            fc2 = fc3
            R0 = R2
            R2 = R3
        else:
            fc0 = fc0
            fc2 = fc3
            R0 = R0
            R2 = R3
    return output


def MAX(vx):
    return np.max([np.max(vx), -np.min(vx)])


def filtered_Facc(Facc, freq, fc, order):
    filtered_Facc = []
    for Fa, f in zip(Facc, freq):
        if f == 0:
            filtered_Facc.append(0.0)
        else:
            filtered_Facc.append(Fa / (np.sqrt(1.0 + (fc / f) ** (2.0 * order))))
    return filtered_Facc


def get_residual(time, disp, target, polynomial_order):
    coef = np.polyfit(time[0 : len(disp.data)], disp.data, polynomial_order)
    fit = []
    for t in time:
        fit.append(np.polyval(coef, t))
    return MAX(fit) / MAX(disp.data) - target
