#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local imports
from gmprocess.metrics.imc.imc import IMC


class Channels(IMC):
    """Class defining steps and invalid imts, for channels."""

    # making invalid IMTs a class variable because
    # 1) it doesn't change with instances
    # 2) information can now be retrieved without
    #    instantiating first
    _invalid_imts = []

    def __init__(self, imc, imt, percentile=None, period=None):
        """
        Args:
            imc (string):
                Intensity measurement component.
            imt (string):
                Intensity measurement type.
            percentile (float):
                Percentile for rotations. Default is None.  Not used by
                Channels.
            period (float):
                Period for fourier amplitude spectra and spectral amplitudes.
                Default is None. Not used by Channels.
        """
        super().__init__(imc, imt, percentile=None, period=None)
        self._steps = {
            "Rotation": "null_rotation",
            "Combination1": "null_combination",
            "Combination2": "null_combination",
        }
