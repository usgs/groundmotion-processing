#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gmprocess.utils.config import get_config


class Reduction(object):
    """Base class for reduction calculations."""

    def __init__(
        self,
        reduction_data,
        bandwidth=None,
        percentile=None,
        period=None,
        smoothing=None,
        interval=[5, 95],
        config=None,
    ):
        """
        Args:
            reduction_data (StationStream):
                Intensity measurement component.
            bandwidth (float):
                Bandwidth for the smoothing operation. Default is None.
            percentile (float):
                Percentile for rotation calculations. Default is None.
            period (float):
                Period for smoothing (Fourier amplitude spectra) calculations.
                Default is None.
            smoothing (string):
                Smoothing type. Default is None.
            interval (list):
                List of length 2 with the quantiles (0-1) for duration interval
                calculation.
        """
        self.period = period
        self.reduction_data = reduction_data
        if config is None:
            config = get_config()
        self.config = config
