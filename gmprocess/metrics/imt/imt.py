#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local imports
from gmprocess.metrics.gather import gather_pgms


class IMT(object):
    """Base class for the IMT classes."""

    def __init__(self, imt, imc, period=None):
        """
        Args:
            imc (string):
                Intensity measurement component.
            imt (string):
                Intensity measurement type.
            period (float):
                Period for fourier amplitude spectra and spectral amplitudes.
                Default is None.
        """
        self.imt = imt.lower()
        self.imc = imc.lower()
        self.period = period
        imts, imcs = gather_pgms()
        self._available_imcs = imcs

    def valid_combination(self, imc):
        """
        Checks whether the combinations of imt and imc is valid.

        Args:
            imc (str):
                Intensity measure component.

        Returns:
            bool: Whether or not the pair is valid.
        """
        imc = imc.lower()
        if imc in self._available_imcs and imc not in self._invalid_imcs:
            return True
        else:
            return False

    @property
    def steps(self):
        """
        Steps for the imt/imc computation.

        Returns:
            self._steps: Steps for the imt/imc computation as a dictionary.
        """
        return self._steps
