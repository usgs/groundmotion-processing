#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third party imports
import numpy as np
from scipy import integrate

# Local imports
from gmprocess.utils.constants import GAL_TO_PCTG
from gmprocess.metrics.reduction.reduction import Reduction

# Hard code percentiles for duration now. Need to make this conigurable.
P_START = 0.0
P_END = 0.7
NBINS = 20


class SortedDuration(Reduction):
    """Class for calculation of sorted duration.

    This code is based on the implementation provided by Mahdi Bahrampouri on
    2/2/2021.
    """

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
        self.result = self.get_sorted_duration()

    def get_sorted_duration(self):
        """
        Performs calculation of arias intensity.

        Returns:
            Dictionary of sorted durations for each channel.
        """
        sorted_durations = {}
        for trace in self.reduction_data:
            dt = trace.stats["delta"]
            # convert from cm/s/s to m/s/s
            acc = trace.data * 0.01

            # Calculate Arias Intensity
            integrated_acc2 = integrate.cumtrapz(acc * acc, dx=dt)
            arias_intensity = integrated_acc2 * np.pi * GAL_TO_PCTG / 2

            # Normalized AI
            ai_norm = arias_intensity / np.max(arias_intensity)

            # Binned intervals
            ai_norm_levels = np.linspace(0, 1, NBINS + 1)
            index = np.searchsorted(ai_norm, ai_norm_levels, side="right")
            dindex = index[1:] - index[:-1]
            D5_75_sorted = sum(np.sort(dindex)[: int(P_END * NBINS)]) * dt

            channel = trace.stats.channel
            sorted_durations[channel] = D5_75_sorted

        return sorted_durations
