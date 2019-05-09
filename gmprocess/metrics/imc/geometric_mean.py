# Local imports
from gmprocess.metrics.imc.imc import IMC


class Geometric_Mean(IMC):
    """Class defining steps and invalid imts, for geometric mean."""
    def __init__(self, imc, imt, percentile=None, period=None):
        """
        Args:
            imc (string): Intensity measurement component.
            imt (string): Intensity measurement type.
            percentile (float): Percentile for rotations. Default is None.
                    Not used by GM.
            period (float): Period for fourier amplitude spectra and
                    spectral amplitudes.  Default is None. Not used by GM.
        """
        super().__init__(imc, imt, percentile=None, period=None)
        self._steps = {
                'Rotation': 'null_rotation',
                'Combination2': 'geometric_mean',
        }
        if imt.startswith('fas'):
            self._steps['Combination1'] = 'geometric_mean'
            self._steps['Combination2'] = 'null_combination'
        self._invalid_imts = ['ARIAS']
