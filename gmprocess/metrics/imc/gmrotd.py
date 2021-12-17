#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gmprocess.metrics.imc.imc import IMC


class GMROTD(IMC):
    """Class defining steps and invalid imts, for GMROTD."""

    # making invalid IMTs a class variable because
    # 1) it doesn't change with instances
    # 2) information can now be retrieved without
    #    instantiating first
    _invalid_imts = ["FAS", "ARIAS"]

    def __init__(self, imc, imt, percentile, period=None):
        """
        Args:
            imc (string):
                Intensity measurement component.
            imt (string):
                Intensity measurement type.
            percentile (float):
                Percentile for rotations.
            period (float):
                Period for fourier amplitude spectra and spectral amplitudes.
                Default is None. Not used by GMROTD.
        """
        super().__init__(imc, imt, percentile=None, period=None)
        self.percentile = percentile
        self._steps = {
            "Rotation": "gmrotd",
            "Combination2": "null_combination",
            "Reduction": "percentile",
        }
