# Local imports
from gmprocess.metrics.gather import gather_pgms
from gmprocess.metrics.metrics_controller_imt.imt import IMT


class FAS(IMT):
    """Class defining steps and invalid imts, for fourier amplitude spectra."""
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
                'Transform2': 'null_transform',
                'Transform3': 'fft',
                'Combination1': 'gm',
                'Reduction': 'smooth_select',
        }
        imts, imcs = gather_pgms()
        self._invalid_imcs = [imc for imc in imcs if imc != 'gm']
