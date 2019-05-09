# Local imports
from gmprocess.metrics.imt.imt import IMT


class SA(IMT):
    """Class defining steps and invalid imts, for spectral amplitudes."""
    def __init__(self, imt, imc, period):
        """
        Args:
            imt (string): Intensity measurement type.
            imc (string): Intensity measurement component.
            period (float): Period for fourier amplitude spectra and
                    spectral amplitudes.
        """
        super().__init__(imt, imc, period=None)
        self._steps = {
                'Transform2': 'oscillator',
                'Transform3': 'null_transform',
                'Combination1': 'null_combination',
                'Reduction': 'max',
        }
        self._invalid_imcs = []
