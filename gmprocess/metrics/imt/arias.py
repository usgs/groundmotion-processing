# Local imports
from gmprocess.metrics.gather import gather_pgms
from gmprocess.metrics.imt.imt import IMT


class Arias(IMT):
    """Class defining steps and invalid imts, for arias intensity."""
    def __init__(self, imt, imc, period=None):
        """
        Args:
            imt (string): Intensity measurement type.
            imc (string): Intensity measurement component.
            period (float): Period for fourier amplitude spectra and
                    spectral amplitudes. Default is None. Not used by Arias.
        """
        super().__init__(imt, imc, period=None)
        self._steps = {
                'Transform2': 'null_transform',
                'Transform3': 'null_transform',
                'Combination1': 'null_combination',
                'Reduction': 'arias',
        }
        imts, imcs = gather_pgms()
        self._invalid_imcs = [imc for imc in imcs if imc != 'arithmetic_mean']
