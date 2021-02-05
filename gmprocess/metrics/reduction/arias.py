#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third party imports
import numpy as np
from scipy import integrate

# Local imports
from gmprocess.utils.constants import GAL_TO_PCTG
from gmprocess.metrics.reduction.reduction import Reduction
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace


class Arias(Reduction):
    """Class for calculation of arias intensity."""

    def __init__(self, reduction_data, bandwidth=None, percentile=None,
                 period=None, smoothing=None, interval=[5, 95]):
        """
        Args:
            reduction_data (obspy.core.stream.Stream or numpy.ndarray):
                Intensity measurement component.
            bandwidth (float):
                Bandwidth for the smoothing operation. Default is None.
            percentile (float):
                Percentile for rotation calculations. Default is None.
            period (float):
                Period for smoothing (Fourier amplitude spectra)
                calculations. Default is None.
            smoothing (string):
                Smoothing type. Default is None.
            interval (list):
                List of length 2 with the quantiles (0-1) for duration interval
                calculation.
        """
        super().__init__(reduction_data, bandwidth=None, percentile=None,
                         period=None, smoothing=None, interval=[5, 95])
        self.arias_stream = None
        self.result = self.get_arias()

    def get_arias(self):
        """
        Performs calculation of arias intensity.

        Returns:
            arias_intensities: Dictionary of arias intensity for each channel.
        """
        arias_intensities = {}
        arias_stream = StationStream([])
        for trace in self.reduction_data:
            dt = trace.stats['delta']
            # convert from cm/s/s to m/s/s
            acc = trace.data * 0.01

            # Calculate Arias Intensity
            integrated_acc2 = integrate.cumtrapz(acc * acc, dx=dt)
            arias_intensity = integrated_acc2 * np.pi * GAL_TO_PCTG / 2

            # Create a copy of stats so we don't modify original data
            stats = trace.stats.copy()
            channel = stats.channel
            stats.standard.units = 'vel'
            stats.npts = len(arias_intensity)
            arias_stream.append(StationTrace(arias_intensity, stats))
            arias_intensities[channel] = np.abs(np.max(arias_intensity))
        self.arias_stream = arias_stream
        return arias_intensities
