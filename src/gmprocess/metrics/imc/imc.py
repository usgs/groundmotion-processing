#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local imports
from gmprocess.metrics.gather import gather_pgms


class IMC(object):
    """Base class for the IMC classes."""

    def __init__(self, imc, imt, percentile=None, period=None):
        """
        Args:
            imc (string):
                Intensity measurement component.
            imt (string):
                Intensity measurement type.
            percentile (float):
                Percentile for rotations. Default is None. Not used by AM.
            period (float):
                Period for fourier amplitude spectra and spectral amplitudes.
                Default is None. Not used by AM.
        """
        self.imc = imc.lower()
        self.imt = imt.lower()
        self.period = period
        self.percentile = percentile
        imts, imcs = gather_pgms()
        self._available_imts = imts

    def valid_combination(self, imt):
        """Checks whether the combinations of imt and imc is valid.

        Args:
            imt: (string):
                Intensity measurement type.
        Returns:
            bool: Whether or not the pair is valid.
        """
        imt = self.imt.lower()
        if imt in self._available_imts and imt not in self._invalid_imts:
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
