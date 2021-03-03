#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local imports
from gmprocess.metrics.rotation.rotation import Rotation


class Rotd(Rotation):
    """Class for computing the ROTD rotation."""

    def __init__(self, rotation_data, event=None):
        """
        Args:
            rotation_data (obspy.core.stream.Stream or numpy.ndarray):
                Intensity measurement component.
            event (ScalarEvent):
                Defines the focal time, geographical location and magnitude of
                an earthquake hypocenter. Default is None.
        """
        super().__init__(rotation_data, event=None)
        self.result = self.get_rotd()

    def get_rotd(self):
        """
        Performs GMROTD rotation.

        Returns:
            rotd: numpy.ndarray of the rotated and combined traces.
        """
        horizontals = self._get_horizontals()
        osc1, osc2 = horizontals[0].data, horizontals[1].data
        rotd = [self.rotate(osc1, osc2, combine=True)]
        return rotd
