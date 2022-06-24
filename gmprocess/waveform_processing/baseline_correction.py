#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from scipy.optimize import curve_fit
from gmprocess.waveform_processing.integrate import get_disp
from gmprocess.utils.config import get_config


def correct_baseline(trace, config=None):
    """
    Performs a baseline correction following the method of Ancheta
    et al. (2013). This removes low-frequency, non-physical trends
    that remain in the time series following filtering.

    Args:
        trace (obspy.core.trace.Trace):
            Trace of strong motion data.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        trace: Baseline-corrected trace.
    """
    if config is None:
        config = get_config()

    # Integrate twice to get the displacement time series
    disp = get_disp(trace, config=config)

    # Fit a sixth order polynomial to displacement time series, requiring
    # that the 1st and 0th order coefficients are zero
    time_values = (
        np.linspace(0, trace.stats.npts - 1, trace.stats.npts) * trace.stats.delta
    )
    poly_cofs = list(curve_fit(_poly_func, time_values, disp.data)[0])
    poly_cofs += [0, 0]

    # Construct a polynomial from the coefficients and compute
    # the second derivative
    polynomial = np.poly1d(poly_cofs)
    polynomial_second_derivative = np.polyder(polynomial, 2)

    # Subtract the second derivative of the polynomial from the
    # acceleration trace
    trace.data -= polynomial_second_derivative(time_values)
    trace.setParameter("baseline", {"polynomial_coefs": poly_cofs})

    return trace


def _poly_func(x, a, b, c, d, e):
    """
    Model polynomial function for polynomial baseline correction.
    """
    return a * x ** 6 + b * x ** 5 + c * x ** 4 + d * x ** 3 + e * x ** 2
