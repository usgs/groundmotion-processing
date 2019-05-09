# Local imports
from gmprocess.metrics.imc.imc import IMC


class Radial_Transverse(IMC):
    """Class defining steps and invalid imts, for radial transverse."""
    def __init__(self, imc, imt, percentile=None, period=None):
        """
        Args:
            imc (string): Intensity measurement component.
            imt (string): Intensity measurement type.
            percentile (float): Percentile for rotations. Default is None.
                    Not used by radial transverse.
            period (float): Period for fourier amplitude spectra and
                    spectral amplitudes.  Default is None. Not used by
                    radial transverse.
        """
        super().__init__(imc, imt, percentile=None, period=None)
        self._steps = {
                'Rotation': 'radial_transverse',
                'Combination2': 'null_combination',
        }
        self._invalid_imts = ['FAS', 'ARIAS']
