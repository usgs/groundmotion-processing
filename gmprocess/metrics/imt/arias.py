#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local imports
from gmprocess.metrics.gather import gather_pgms
from gmprocess.metrics.imt.imt import IMT


class Arias(IMT):
    """Class defining steps and invalid imts, for arias intensity."""

    # making invalid IMCs a class variable because
    # 1) it doesn't change with instances
    # 2) information can now be retrieved without
    #    instantiating first
    imts, imcs = gather_pgms()
    _invalid_imcs = ["gmrotd", "rotd"]

    def __init__(self, imt, imc, period=None):
        """
        Args:
            imt (string):
                Intensity measurement type.
            imc (string):
                Intensity measurement component.
            period (float):
                Period for fourier amplitude spectra and spectral amplitudes.
                Default is None. Not used by Arias.
        """
        super().__init__(imt, imc, period=None)
        self._steps = {
            "Transform2": "null_transform",
            "Transform3": "null_transform",
            "Combination1": "null_combination",
            "Reduction": "arias",
        }
