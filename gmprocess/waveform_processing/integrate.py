#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from scipy.integrate import cumtrapz


def get_disp(tr, config=None):
    """Integrate acceleration to displacement.

    Args:
        tr (StationTrace):
            Trace of acceleration data. This is the trace where the Cache values will
            be set.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationTrace.

    """
    acc = tr.copy()
    try:
        disp = acc.integrate(config=config).integrate(config=config)
    except Exception as e:
        raise e
    return disp


def get_vel(tr, config=None):
    """Integrate acceleration to velocity.

    Args:
        tr (StationTrace):
            Trace of acceleration data. This is the trace where the Cache values will
            be set.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationTrace.

    """
    acc = tr.copy()
    try:
        vel = acc.integrate(config=config)
    except Exception as e:
        raise e
    return vel
