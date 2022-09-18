#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third party imports
import numpy as np
from obspy.geodetics.base import gps2dist_azimuth
from obspy.core.stream import Stream

# Local imports
from gmprocess.metrics.rotation.rotation import Rotation
from gmprocess.core.stationstream import StationStream


class Radial_Transverse(Rotation):
    """Class for computing the Radial Transverse rotation."""

    def __init__(self, rotation_data, event, config=None):
        """
        Args:
            rotation_data (obspy.core.stream.Stream or numpy.ndarray):
                Intensity measurement component.
            event (ScalarEvent):
                Defines the focal time, geographical location and
                magnitude of an earthquake hypocenter. Default is None.
            config (dict):
                Configuration options.
        """
        super().__init__(rotation_data, event=event, config=config)
        self.result = self.get_radial_transverse()

    def get_radial_transverse(self):
        """
        Performs radial transverse rotation.

        Returns:
            radial_transverse: StationStream with the radial and
                    transverse components.
        """
        st_copy = self.rotation_data.copy()
        st_n = st_copy.select(component="[N1]")
        st_e = st_copy.select(component="[E2]")

        # Check that we have one northing and one easting channel
        if len(st_e) != 1 or len(st_n) != 1:
            raise Exception(
                "Radial_Transverse: Stream must have one north and one east channel."
            )

        # Check that the orientations are orthogonal
        ho1 = st_e[0].stats.standard.horizontal_orientation
        ho2 = st_n[0].stats.standard.horizontal_orientation
        if abs(ho1 - ho2) not in [90, 270]:
            raise Exception("Radial_Transverse: Channels must be orthogonal.")

        # Check that the lengths of the two channels are the same
        if st_e[0].stats.npts != st_n[0].stats.npts:
            raise Exception(
                "Radial_Transverse: East and north channels must have same length."
            )

        # First, rotate to North-East components if not already
        if st_n[0].stats.standard.horizontal_orientation != 0:
            az_diff = 360 - st_n[0].stats.standard.horizontal_orientation
            az_diff = np.deg2rad(az_diff)
            rotation_matrix = np.array(
                [
                    [np.cos(az_diff), np.sin(az_diff)],
                    [-np.sin(az_diff), np.cos(az_diff)],
                ]
            )
            data = np.array([st_n[0].data, st_e[0].data])
            newdata = np.matmul(rotation_matrix, data)

            st_n[0].data = newdata[0]
            st_e[0].data = newdata[1]

        st_n[0].stats.channel = st_n[0].stats.channel[:-1] + "N"
        st_e[0].stats.channel = st_n[0].stats.channel[:-1] + "E"

        # For some reason the rotation does not update the channel
        # name in the rotation if it is not an obspy stream
        ne_stream = Stream([st_n[0], st_e[0]])
        # Calculate back azimuth and perform rotation to radial and transverse
        baz = gps2dist_azimuth(
            st_e[0].stats.coordinates.latitude,
            st_e[0].stats.coordinates.longitude,
            self.event.latitude,
            self.event.longitude,
        )[1]
        ne_stream.rotate(method="NE->RT", back_azimuth=baz)
        radial_transverse = StationStream(
            [ne_stream[0], ne_stream[1]], config=self.config
        )
        return radial_transverse
