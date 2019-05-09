# Local imports
from gmprocess.metrics.imc.imc import IMC


class Greater_Of_Two_Horizontals(IMC):
    """Class defining steps and invalid imts, for greater of two horizontals."""
    def __init__(self, imc, imt, percentile=None, period=None):
        """
        Args:
            imc (string): Intensity measurement component.
            imt (string): Intensity measurement type.
            percentile (float): Percentile for rotations. Default is None.
                    Not used by greater of two horizontals.
            period (float): Period for fourier amplitude spectra and
                    spectral amplitudes.  Default is None. Not used by
                    greater of two horizontals.
        """
        super().__init__(imc, imt, percentile=None, period=None)
        self._steps = {
                'Rotation': 'null_rotation',
                'Combination2': 'greater_of_two_horizontals',
        }
        self._invalid_imts = ['ARIAS', 'FAS']
