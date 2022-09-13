#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local imports
from gmprocess.metrics.exception import PGMException


class Transform(object):
    """Base class for rotation calculations."""

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
        self.config = config
        self.transform_data = transform_data

    def _get_horizontals(self):
        """
        Gets the two horizontal components.

        Returns:
            horizontal_channels: list of horizontal channels
                    (obspy.core.trac.Trace).

        Raises:
            PGMException: if there are less than or greater than two
                    horizontal channels, or if the lengths of the channels
                    are different.
        """
        horizontal_channels = []
        for trace in self.transform_data:
            # Group all of the max values from traces without
            # Z in the channel name
            if "Z" not in trace.stats["channel"].upper() and trace.passed:
                horizontal_channels += [trace]
        # Test the horizontals
        if len(horizontal_channels) > 2:
            raise PGMException("Rotation: More than two horizontal channels.")
        elif len(horizontal_channels) < 2:
            raise PGMException("Rotation: Less than two horizontal channels.")
        elif len(horizontal_channels[0].data) != len(horizontal_channels[1].data):
            raise PGMException("Rotation: Horizontal channels have different lengths.")
        return horizontal_channels
