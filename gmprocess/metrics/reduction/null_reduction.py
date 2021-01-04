#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local imports
from gmprocess.metrics.reduction.reduction import Reduction


class Null_Reduction(Reduction):
    """"Class for null reduction calculation. This perfoms no action
        other than returning the input reduction_data."""

    def __init__(self, reduction_data, bandwidth=None, percentile=None,
                 period=None, smoothing=None):
        """
        Args:
            reduction_data (obspy.core.stream.Stream or numpy.ndarray):
                Intensity measurement component.
            percentile (float):
                Percentile for rotation calculations. Default is None.
            period (float):
                Period for smoothing (Fourier amplitude spectra) calculations.
                Default is None.
            smoothing (string):
                Smoothing type. Default is None.
            bandwidth (float):
                Bandwidth for the smoothing operation. Default is None.
        """
        super().__init__(reduction_data, bandwidth=None, percentile=None,
                         period=None, smoothing=None)
        self.result = self.get_reduction_data()

    def get_reduction_data(self):
        """
        Returns:
            self.reduction_data: The original input without alteration.
        """
        return self.reduction_data
