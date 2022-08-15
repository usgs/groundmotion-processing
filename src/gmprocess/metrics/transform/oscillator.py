#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local import
from gmprocess.metrics.oscillators import get_spectral
from gmprocess.metrics.transform.transform import Transform


class oscillator(Transform):
    """Class for computing the oscillator for a given period."""

    def __init__(
        self,
        transform_data,
        damping,
        period,
        times,
        max_period,
        allow_nans,
        bandwidth,
        config,
    ):
        """
        Args:
            transform_data (StationStream):
                Intensity measurement component.
            damping (float):
                Damping for spectral amplitude calculations.
            period (float):
                Period for spectral amplitude calculations.
            times (numpy.ndarray):
                Times for the spectral amplitude calculations.
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
        self.period = period
        self.damping = damping
        self.times = times
        self.result = self.get_oscillator(config)

    def get_oscillator(self, config=None):
        """
        Calculated the oscillator of each trace's data.

        Args:
            config (dict):
                Configuration options.

        Returns:
            spectrals: StationStream or numpy.ndarray with the oscillator data.
        """
        spectrals = get_spectral(
            self.period,
            self.transform_data,
            damping=self.damping,
            times=self.times,
            config=config,
        )
        return spectrals
