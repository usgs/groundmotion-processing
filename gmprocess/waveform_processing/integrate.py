#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from scipy.integrate import cumtrapz


def get_disp(tr, method="frequency_domain"):
    """Integrate acceleration to displacement.

    Args:
        tr (StationTrace):
            Trace of acceleration data. This is the trace where the Cache values will
            be set.
        method (string):
            Method used to perform integration. Options are "frequency_domain",
            "time_domain_0init" or "time_domain_0init_0mean".

    Returns:
        StationTrace.

    """
    acc = tr.copy()
    acc.detrend("demean")
    acc.taper(max_percentage=0.05, type="hann", side="both")

    if method == "frequency_domain":
        disp = acc.integrate(frequency=True).integrate(frequency=True)

    elif method == "time_domain_0init":
        disp = acc.integrate().integrate()

    elif method == "time_domain_0init_0mean":
        disp = acc.integrate().integrate(demean=True)
    else:
        raise ValueError(
            "Improper integration method specified in config. "
            "Must be one of 'frequency_domain', 'time_domain_0init' or "
            "'time_domain_0init_0mean'"
        )

    return disp


def get_vel(tr, method="frequency_domain"):
    """Integrate acceleration to velocity.

    Args:
        tr (StationTrace):
            Trace of acceleration data. This is the trace where the Cache values will
            be set.
        method (string):
            Method used to perform integration, specified in the config file. Options
            are "frequency_domain", "time_domain_0init" or "time_domain_0init_0mean".

    Returns:
        StationTrace.

    """
    acc = tr.copy()

    if method == "frequency_domain":
        vel = acc.integrate(frequency=True)

    elif method == "time_domain_0init":
        vel = acc.integrate()

    elif method == "time_domain_0init_0mean":
        vel = acc.integrate(demean=True)
    else:
        raise ValueError(
            "Improper integration method specified in config. Must be one of "
            "'frequency_domain', 'time_domain_0init' or 'time_domain_0init_0mean'"
        )

    return vel
