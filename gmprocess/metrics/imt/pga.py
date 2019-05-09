# Local imports
from gmprocess.metrics.imt.imt import IMT


class PGA(IMT):
    """Class defining steps and invalid imts, for peak ground acceleration."""
    def __init__(self, imt, imc, period=None):
        """
        Args:
            imt (string): Intensity measurement type.
            imc (string): Intensity measurement component.
            period (float): Period for fourier amplitude spectra and
                    spectral amplitudes. Default is None. Not used by PGA.
        """
        super().__init__(imt, imc, period=None)
        self._steps = {
                'Transform2': 'null_transform',
                'Transform3': 'null_transform',
                'Combination1': 'null_combination',
                'Reduction': 'max',
        }
        self._invalid_imcs = []
