#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third party imports
import numpy as np
from scipy import integrate

# Local imports
from gmprocess.utils.constants import GAL_TO_PCTG
from gmprocess.metrics.reduction.reduction import Reduction


class Duration(Reduction):
    """Class for calculation of duration."""

    def __init__(
        self,
        reduction_data,
        bandwidth=None,
        percentile=None,
        period=None,
        smoothing=None,
        interval=None,
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
        self.interval = interval
        self.result = self.get_duration()

    def get_duration(self):
        """
        Performs calculation of arias intensity.

        Returns:
            durations: Dictionary of durations for each channel.
        """
        durations = {}
        for trace in self.reduction_data:
            dt = trace.stats["delta"]
            # convert from cm/s/s to m/s/s
            acc = trace.data * 0.01
            # times = trace.times()
            times = np.linspace(
                0.0, trace.stats.endtime - trace.stats.starttime, trace.stats.npts
            )

            # Calculate Arias Intensity
            integrated_acc2 = integrate.cumtrapz(acc * acc, dx=dt)
            arias_intensity = integrated_acc2 * np.pi * GAL_TO_PCTG / 2

            # Normalized AI
            ai_norm = arias_intensity / np.max(arias_intensity)

            ind0 = np.argmin(np.abs(ai_norm - self.interval[0] / 100.0))
            ind1 = np.argmin(np.abs(ai_norm - self.interval[1] / 100.0))

            dur = times[ind1] - times[ind0]
            channel = trace.stats.channel
            durations[channel] = dur

        return durations
