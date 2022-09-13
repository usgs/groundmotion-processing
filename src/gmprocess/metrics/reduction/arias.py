#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third party imports
import numpy as np

# Local imports
from gmprocess.utils.constants import GAL_TO_PCTG
from gmprocess.metrics.reduction.reduction import Reduction
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace


class Arias(Reduction):
    """Class for calculation of arias intensity."""

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
                Period for smoothing (Fourier amplitude spectra)
                calculations. Default is None.
            smoothing (string):
                Smoothing type. Default is None.
            interval (list):
                List of length 2 with the quantiles (0-1) for duration interval
                calculation.
            config (dict):
                Config dictionary.
        """
        super().__init__(
            reduction_data=reduction_data,
            bandwidth=bandwidth,
            percentile=percentile,
            period=period,
            smoothing=smoothing,
            interval=interval,
            config=config,
        )
        self.arias_stream = None
        self.result = self.get_arias(config=config)

    def get_arias(self, config=None):
        """
        Performs calculation of arias intensity.

        Args:
            config (dict):
                Config options.

        Returns:
            arias_intensities: Dictionary of arias intensity for each channel.
        """
        arias_intensities = {}
        arias_stream = StationStream([], config=config)
        for trace in self.reduction_data:
            tr = trace.copy()
            # convert from cm/s/s to m/s/s
            tr.data *= 0.01
            # square accel
            tr.data *= tr.data

            # Calculate Arias Intensity
            tr.integrate(self.config)
            arias_intensity = tr.data * np.pi * GAL_TO_PCTG / 2

            # Create a copy of stats so we don't modify original data
            stats = trace.stats.copy()
            channel = stats.channel
            stats.standard.units_type = "vel"
            stats.npts = len(arias_intensity)
            arias_stream.append(StationTrace(arias_intensity, stats))
            arias_intensities[channel] = np.abs(np.max(arias_intensity))
        self.arias_stream = arias_stream
        return arias_intensities
