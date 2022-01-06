#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from scipy.integrate import cumtrapz
from gmprocess.utils.config import get_config


def get_disp(tr, method="frequency_domain"):

    """Integrate acceleration to displacement using the method chosen in the config file.

    Args:
    tr (StationTrace):
        Trace of acceleration data. This is the trace where the Cache values will be set.
    method (string):
        method used to perform integration, specified in the config file.
        Options are "frequency_domain", "time_domain_0init" or "time_domain_0init_0mean"

    Returns:
        StationTrace.

    """
    tr_copy = tr.copy()
    tr_copy.detrend("demean")
    tr_copy = tr_copy.taper(max_percentage=0.05, type="hann", side="both")

    if method == "frequency_domain":
        N = len(tr_copy.data)
        Facc = np.fft.rfft(tr_copy.data, n=N)
        freq = np.fft.rfftfreq(N, tr_copy.stats.delta)
        Fdisp = []
        for facc, f in zip(Facc, freq):
            if f == 0:
                Fdisp.append(0.0)
            else:
                Fdisp.append(
                    (facc / 100) / (2.0j * np.pi * f) ** 2
                )  # convert from cm/s^2 to m/s^2
        disp = np.fft.irfft(Fdisp, n=N) * 100  # convert back to cm
        return disp

    elif method == "time_domain_0init":
        disp = cumtrapz(
            cumtrapz(tr_copy.data, dx=tr.stats.delta, initial=0),
            dx=tr.stats.delta,
            initial=0,
        )
        return disp

    elif method == "time_domain_0init_0mean":
        vel = cumtrapz(tr_copy.data, dx=tr_copy.stats.delta, initial=0)
        vel -= np.mean(vel)
        disp = cumtrapz(vel, dx=tr_copy.stats.delta, initial=0)
        return disp
    else:
        raise ValueError(
            "Improper integration method specified in config. Must be one of 'frequency_domain', 'time_domain_0init' or 'time_domain_0init_0mean'"
        )


def get_vel(tr, method="frequency_domain"):

    """Integrate acceleration to velocity using the method chosen in the config file.

    Args:
    tr (StationTrace):
        Trace of acceleration data. This is the trace where the Cache values will be set.
    method (string):
        method used to perform integration, specified in the config file.
        Options are "frequency_domain", "time_domain_0init" or "time_domain_0init_0mean"

    Returns:
        StationTrace.

    """
    tr_copy = tr.copy()

    if method == "frequency_domain":
        N = len(tr_copy.data)
        Facc = np.fft.rfft(tr_copy.data, n=N)
        freq = np.fft.rfftfreq(N, tr_copy.stats.delta)
        Fvel = []
        for facc, f in zip(Facc, freq):
            if f == 0:
                Fvel.append(0.0)
            else:
                Fvel.append(
                    (facc / 100) / (2.0j * np.pi * f)
                )  # convert from cm/s^2 to m/s^2
        vel = np.fft.irfft(Fvel, n=N) * 100  # convert back to cm/s
        return vel

    elif method == "time_domain_0init":
        vel = cumtrapz(tr_copy.data, dx=tr.stats.delta, initial=0)
        return vel

    elif method == "time_domain_0init_0mean":
        tr_copy.data -= np.mean(tr_copy.data)
        vel = cumtrapz(tr_copy.data, dx=tr_copy.stats.delta, initial=0)
        return vel
    else:
        raise ValueError(
            "Improper integration method specified in config. Must be one of 'frequency_domain', 'time_domain_0init' or 'time_domain_0init_0mean'"
        )
