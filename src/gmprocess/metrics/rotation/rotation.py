#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third party imports
import numpy as np

# Local imports
from gmprocess.metrics.exception import PGMException


class Rotation(object):
    """Base class for rotation calculations."""

    def __init__(self, rotation_data, event=None, config=None):
        """
        Args:
            rotation_data (obspy.core.stream.Stream or numpy.ndarray):
                Intensity measurement component.
            event (ScalarEvent):
                Defines the focal time, geographical location and magnitude of
                an earthquake hypocenter. Default is None.
            config (dict):
                Configuration options.
        """
        self.rotation_data = rotation_data
        self.event = event
        self.config = config

    def _get_horizontals(self):
        """
        Gets the two horizontal components.

        Returns:
            horizontal_channels: list of horizontal channels
            (obspy.core.trac.Trace).

        Raises:
            PGMException: if there are less than or greater than two
                horizontal channels.
        """
        horizontal_channels = []
        for trace in self.rotation_data:
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

    def get_max(self, tr1, pick_peak, tr2=None, percentiles=50):
        """
        Finds the maximum from traces and either picks the geometric mean,
        arithmetic mean, or maximum of the two. The two input can either be
        1D traces, or 2D arrays.

        For the 2D array case, the number of rows must be the number of traces,
        and the numer of columns is the number of samples in the trace.
        The following assumptions are made regarding the 2D array:
            1) The rows in each matrix are the same component at different
               rotation at different angles.
            2) If tr2 is provided, the orientation of the trace in each row is
               orthogonal to the analagous row in tr1
            3) The traces that constitute tr1 and tr2 are both
               horizontal components.

        Args:
            tr1 (obspy.core.trace.Trace or 2D array):
                Trace 1, either 1D trace or 2D matrix of rotated components.
            tr2 (obspy.core.trace.Trace or 2D array):
                Trace 2, either 1D trace or or 2D matrix of rotated components.
                Default is None.
            pick_peak (str):
                The choice for either geometric mean, arithmetic or maximum.
                 The valid strings are:
                    - "gm" for geometric mean
                    - "am" for arithmetic mean
                    - "max" for maximum
            percentiles (list):
                Percentile(s) to return the requested values. Default is 50.

        Returns:
            If 1D input:
                Returns a singular,  scalar value for the requested pick_peak.
            If 2D input:
                Returns a list of the maximum values, as well as the singular
                value at the requested percentile.
        """

        # Check if valid trace dimensions were provided, and determine if we're
        # working with 1D or 2D traces. Trace 1 and Trace 2 must have the same
        # dimension (either both 1D or 2D).
        if tr2 is None:
            if len(tr1.shape) == 1:
                input_dim = "1D"
            elif len(tr1.shape) == 2:
                input_dim = "2D"
            else:
                raise PGMException("Trace one must be either 1D or 2D.")
        else:
            if len(tr1.shape) != len(tr2.shape):
                raise PGMException("Traces must have the same dimensions.")
            elif len(tr1.shape) == 1:
                input_dim = "1D"
            elif len(tr1.shape) == 2:
                input_dim = "2D"
            else:
                raise PGMException("Traces must be either 1D or 2D.")

        # Set the axis from which to pull the maximums based on
        # the input dimension.
        if input_dim == "1D":
            axis = 0
        else:
            axis = 1

        # Geometric mean
        if pick_peak.lower() == "gm":
            if tr2 is None:
                raise PGMException("Two traces must be provided to find mean.")
            tr1_max = np.amax(tr1, axis)
            tr2_max = np.amax(tr2, axis)
            geo_means = np.sqrt(tr1_max * tr2_max)

            if input_dim == "1D":
                return geo_means
            else:
                return geo_means, np.percentile(geo_means, percentiles)

        # Arithmetic mean
        elif pick_peak.lower() == "am":
            if tr2 is None:
                raise PGMException("Two traces must be provided to find mean.")
            tr1_max = np.amax(tr1, axis)
            tr2_max = np.amax(tr2, axis)
            arith_means = 0.5 * (tr1_max + tr2_max)

            if input_dim == "1D":
                return arith_means
            else:
                return arith_means, np.percentile(arith_means, percentiles)

        # Maximum
        elif pick_peak.lower() == "max":
            if tr2 is not None:
                tr1_max = np.amax(np.abs(tr1), axis)
                tr2_max = np.amax(np.abs(tr2), axis)

                # Maximum of two horizontals
                if input_dim == "1D":
                    return np.amax([tr1_max, tr2_max])
                else:
                    maximums = []
                    for idx, val in enumerate(tr1_max):
                        max_val = np.max([val, tr2_max[idx]])
                        maximums.append(max_val)
                    return maximums, np.percentile(maximums, percentiles)
            else:
                maximums = np.amax(np.abs(tr1), axis)
                if input_dim == "1D":
                    return maximums
                else:
                    return maximums, np.percentile(maximums, percentiles)
        else:
            raise PGMException("Not a valid pick for the peak.")

    def rotate(self, tr1, tr2, combine=False, delta=1.0):
        """
        Rotates a trace through 180 degrees to obtain the
        data at each degree.

        Args:
            tr1 (ndarray):
                Array of trace data.
            tr2 (ndarray):
                Array of trace data.
            combine (bool):
                Whether rotated traces should be combined. Default is False.
            delta (float):
                Delta degrees which will determine the number of rows
                for the matrix of rotated components.
                Default is 1.0

        Returns:
            numpy.ndarray: Array of data at each degree.
        """

        if combine:
            max_deg = 180
        else:
            max_deg = 90

        num_rows = int(max_deg * (1.0 / delta) + 1)
        degrees = np.deg2rad(np.linspace(0, max_deg, num_rows)).reshape((-1, 1))
        cos_deg = np.cos(degrees)
        sin_deg = np.sin(degrees)

        td1 = np.reshape(tr1, (1, -1))
        td2 = np.reshape(tr2, (1, -1))

        if combine:
            # Calculate GMs
            rot = td1 * cos_deg + td2 * sin_deg
            return rot
        else:
            # Calculate GMs with rotation
            osc1_rot = td1 * cos_deg + td2 * sin_deg
            osc2_rot = -td1 * sin_deg + td2 * cos_deg
            return osc1_rot, osc2_rot
