#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local imports
from gmprocess.metrics.transform.transform import Transform
from gmprocess.core.stationstream import StationStream


class Integrate(Transform):
    """Class for computing the integral."""

    def __init__(
        self,
        transform_data,
        damping=None,
        period=None,
        times=None,
        max_period=None,
        allow_nans=None,
        bandwidth=None,
        config=None,
    ):
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
            allow_nans (bool):
                Should nans be allowed in the smoothed spectra. If False, then
                the number of points in the FFT will be computed to ensure
                that nans will not result in the smoothed spectra.
            config (dict):
                Configuration options.
        """
        super().__init__(
            transform_data,
            damping=damping,
            period=period,
            times=times,
            max_period=max_period,
            allow_nans=allow_nans,
            bandwidth=bandwidth,
            config=config,
        )
        self.result = self.get_integral(config=config)

    def get_integral(self, config=None):
        """
        Calculated the integral of each trace's data.

        Returns:
            stream: StationStream with the integrated data.
        """
        stream = StationStream([], config=self.config)
        for trace in self.transform_data:
            integrated_trace = trace.copy().integrate(config=config)
            stream.append(integrated_trace)
        return stream
