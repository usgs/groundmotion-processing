#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third party imports
import numpy as np

# Local imports
from gmprocess.metrics.exception import PGMException
from gmprocess.metrics.reduction.reduction import Reduction


class Percentile(Reduction):
    def __init__(self, reduction_data, bandwidth=None, percentile=None,
                 period=None, smoothing=None, interval=[5, 95]):
        """
        Args:
            reduction_data (obspy.core.stream.Stream or numpy.ndarray):
                Intensity measurement component.
            bandwidth (float):
                Bandwidth for the smoothing operation. Default is None.
            percentile (float):
                Percentile for rotation calculations.
            period (float):
                Period for smoothing (Fourier amplitude spectra) calculations.
                Default is None.
            smoothing (string):
                Smoothing type. Default is None.
            interval (list):
                List of length 2 with the quantiles (0-1) for duration interval
                calculation.

        Raises:
            PGMException: if the percentile value is None.
        """
        super().__init__(reduction_data, bandwidth=None, percentile=None,
                         period=None, smoothing=None)
        if percentile is None:
            raise PGMException('Percentile: The percentile value must '
                               'be defined and of type float or int.')
        self.percentile = percentile
        self.result = self.get_percentile()

    def get_percentile(self):
        """
        Performs calculation of percentile.

        Returns:
            percentiles: Dictionary of percentiles for each channel.
        """
        percentiles = {}
        if len(self.reduction_data) == 3:
            for tr in self.reduction_data:
                percentiles[tr.channel] = np.percentile(
                    tr.data, self.percentile)
        elif len(self.reduction_data) == 1:
            maximums = np.amax(np.abs(self.reduction_data[0]), 1)
            percentiles[''] = np.percentile(maximums, self.percentile)
        else:
            percentiles[''] = np.percentile(
                self.reduction_data, self.percentile)
        return percentiles
