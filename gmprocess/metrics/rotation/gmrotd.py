#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third party imports
import numpy as np

# Local imports
from gmprocess.metrics.rotation.rotation import Rotation


class GMROTD(Rotation):
    """Class for computing the GMROTD rotation."""

    def __init__(self, rotation_data, event=None):
        """
        Args:
            rotation_data (obspy.core.stream.Stream or numpy.ndarray):
                Intensity measurement component.
            event (ScalarEvent): Defines the focal time, geographical
                location and magnitude of an earthquake hypocenter.
                    Default is None.
        """
        super().__init__(rotation_data, event=None)
        self.result = self.get_gmrotd()

    def get_gmrotd(self):
        """
        Performs GMROTD rotation.

        Returns:
            rotd: numpy.ndarray of the rotated and combined traces.
        """
        horizontals = self._get_horizontals()
        osc1, osc2 = horizontals[0].data, horizontals[1].data
        osc1_rot, osc2_rot = self.rotate(osc1, osc2, combine=False)
        osc1_max = np.amax(osc1_rot, 1)
        osc2_max = np.amax(osc2_rot, 1)
        rotd = np.sqrt(osc1_max * osc2_max)
        return rotd
