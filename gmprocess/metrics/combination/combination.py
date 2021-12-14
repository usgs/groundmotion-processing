#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third party imports
from obspy.core.stream import Stream

# Local imports
from gmprocess.metrics.exception import PGMException
from gmprocess.core.stationstream import StationStream


class Combination(object):
    """Base class for combination calculations."""

    def __init__(self, combination_data):
        """
        Args:
            combination_data (obspy.core.stream.Stream or numpy.ndarray):
                Data for calculation.
        """
        self.combination_data = combination_data

    def _get_horizontals(self):
        """
        Gets the two horizontal components.

        Returns:
            horizontal_channels:
                list of horizontal channels (obspy.core.trac.Trace or float).

        Raises:
            PGMException: if there are less than or greater than two
                horizontal channels, or if the length of the traces are
                not equal.
        """
        horizontal_channels = []
        if isinstance(self.combination_data, (StationStream, Stream)):
            for trace in self.combination_data:
                # Group all of the max values from traces without
                # Z in the channel name
                if "Z" not in trace.stats["channel"].upper():
                    horizontal_channels += [trace]
            # Test the horizontals
            if len(horizontal_channels) > 2:
                raise PGMException("Combination: More than two horizontal channels.")
            elif len(horizontal_channels) < 2:
                raise PGMException("Combination: Less than two horizontal channels.")
            elif len(horizontal_channels[0].data) != len(horizontal_channels[1].data):
                raise PGMException(
                    "Combination: Horizontal channels have different lengths."
                )
        elif isinstance(self.combination_data, dict):
            for channel_key in self.combination_data:
                # Group all of the max values from traces without
                # Z in the channel name
                if "Z" not in channel_key:
                    horizontal_channels += [self.combination_data[channel_key]]
            if len(horizontal_channels) > 2:
                raise PGMException("Combination: More than two horizontal channels.")
            elif len(horizontal_channels) < 2:
                raise PGMException("Combination: Less than two horizontal channels.")
        else:
            raise PGMException("Combination: Invalid input data type")
        return horizontal_channels
