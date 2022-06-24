#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local imports
from gmprocess.metrics.reduction.reduction import Reduction


class Null_Reduction(Reduction):
    """Class for null reduction calculation. This perfoms no action
    other than returning the input reduction_data."""

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
            reduction_data (obspy.core.stream.Stream or numpy.ndarray):
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
            config (dict):
                Config dictionary.
        """
        super().__init__(
            reduction_data,
            bandwidth=bandwidth,
            percentile=percentile,
            period=period,
            smoothing=smoothing,
            interval=interval,
            config=config,
        )
        self.result = self.get_reduction_data()

    def get_reduction_data(self):
        """
        Returns:
            self.reduction_data: The original input without alteration.
        """
        return self.reduction_data
