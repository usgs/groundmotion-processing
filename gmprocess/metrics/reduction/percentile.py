#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third party imports
import numpy as np

# Local imports
from gmprocess.metrics.exception import PGMException
from gmprocess.metrics.reduction.reduction import Reduction


class Percentile(Reduction):
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
            reduction_data (StationStream or ndarray):
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
            config (dict):
                Config dictionary.
        Raises:
            PGMException: if the percentile value is None.
        """
        super().__init__(
            reduction_data,
            bandwidth=bandwidth,
            percentile=percentile,
            period=period,
            smoothing=smoothing,
            config=config,
        )
        if percentile is None:
            raise PGMException(
                "Percentile: The percentile value must "
                "be defined and of type float or int."
            )
        self.period = period
        self.percentile = percentile
        self.result = self.get_percentile()

    def get_percentile(self):
        """
        Performs calculation of percentile.

        Returns:
            percentiles: Dictionary of percentiles for each channel.
        """
        stream = self.reduction_data
        if isinstance(stream, np.ndarray):
            rdata = stream
        elif self.period is not None:
            if "rotated_oscillator" in stream.getStreamParamKeys():
                rdata = stream.getStreamParam("rotated_oscillator")
            else:
                raise ValueError("Missing rotated oscillator response.")
        elif "rotated" in stream.getStreamParamKeys():
            rdata = stream.getStreamParam("rotated")
        else:
            raise ValueError(
                "Percentile reduction can only be applied after a rotation "
                "has been applied to the data."
            )

        percentiles = {}
        if len(rdata) == 3:
            for tr in rdata:
                percentiles[tr.channel] = np.percentile(tr.data, self.percentile)
        elif len(rdata) == 1:
            maximums = np.amax(np.abs(rdata[0]), 1)
            percentiles[""] = np.percentile(maximums, self.percentile)
        else:
            percentiles[""] = np.percentile(rdata, self.percentile)
        return percentiles
