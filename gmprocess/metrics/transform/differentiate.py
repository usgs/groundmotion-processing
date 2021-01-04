#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third party imports
from gmprocess.metrics.transform.transform import Transform
from gmprocess.core.stationstream import StationStream


class Differentiate(Transform):
    """Class for computing the derivative."""

    def __init__(self, transform_data, damping=None, period=None, times=None,
                 max_period=None, allow_nans=None, bandwidth=None):
        """
        Args:
            transform_data (obspy.core.stream.Stream or numpy.ndarray):
                Intensity measurement component.
            damping (float):
                Damping for spectral amplitude calculations. Default is None.
            period (float):
                Period for spectral amplitude calculations. Default is None.
            times (numpy.ndarray):
                Times for the spectral amplitude calculations. Default is None.
        """
        super().__init__(transform_data, damping=None, period=None, times=None,
                         max_period=None, allow_nans=None, bandwidth=None)
        self.result = self.get_derivative()

    def get_derivative(self):
        """
        Calculated the derivative of each trace's data.

        Returns:
            stream: StationStream with the differentiated data.
        """
        stream = StationStream([])
        for trace in self.transform_data:
            differentiated_trace = trace.copy().differentiate()
            differentiated_trace.stats['units'] = 'acc'
            stream.append(differentiated_trace)
        return stream
