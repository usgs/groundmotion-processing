#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local imports
from gmprocess.metrics.gather import gather_pgms
from gmprocess.metrics.imt.imt import IMT

imts, imcs = gather_pgms()


class FAS(IMT):
    """Class defining steps and invalid imts, for fourier amplitude spectra."""

    # making invalid IMCs a class variable because
    # 1) it doesn't change with instances
    # 2) information can now be retrieved without
    #    instantiating first
    _invalid_imcs = ["gmrotd", "rotd"]

    def __init__(self, imt, imc, period):
        """
        Args:
            imt (string):
                Intensity measurement type.
            imc (string):
                Intensity measurement component.
            period (float):
                Period for fourier amplitude spectra and
                spectral amplitudes.
        """
        super().__init__(imt, imc, period=None)
        self._steps = {
            "Transform2": "null_transform",
            "Transform3": "fft",
            "Reduction": "smooth_select",
        }
