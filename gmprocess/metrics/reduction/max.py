#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third party imports
import numpy as np
from obspy import Stream

# Local imports
from gmprocess.metrics.reduction.reduction import Reduction
from gmprocess.core.stationstream import StationStream


class Max(Reduction):
    """Class for calculation of maximum value."""

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
        self.result = self.get_max()

    def get_max(self):
        """
        Performs calculation of maximum value.

        Returns:
            maximums: Dictionary of maximum value for each channel.
        """
        maximums = {}
        times = {}
        if isinstance(self.reduction_data, (Stream, StationStream)):
            for trace in self.reduction_data:
                if trace.stats.standard.units_type == "acc":
                    key = "pga_time"
                elif trace.stats.standard.units_type == "vel":
                    key = "pgv_time"
                elif trace.stats.standard.units_type == "disp":
                    key = "pgd_time"
                else:
                    key = "peak_time"
                idx = np.argmax(np.abs(trace.data))
                dtimes = np.linspace(
                    0.0, trace.stats.endtime - trace.stats.starttime, trace.stats.npts
                )
                dtime = dtimes[idx]
                max_value = np.abs(trace.data[idx])
                max_time = trace.stats.starttime + dtime
                maximums[trace.stats.channel] = max_value
                times[trace.stats.channel] = {key: max_time}
            return maximums, times
        else:
            for chan in self.reduction_data:
                maximums[chan] = np.abs(self.reduction_data[chan]).max()
            return maximums
