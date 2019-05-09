from gmprocess.metrics.imc.imc import IMC


class GMROTD(IMC):
    """Class defining steps and invalid imts, for GMROTD."""
    def __init__(self, imc, imt, percentile, period=None):
        """
        Args:
            imc (string): Intensity measurement component.
            imt (string): Intensity measurement type.
            percentile (float): Percentile for rotations.
            period (float): Period for fourier amplitude spectra and
                    spectral amplitudes.  Default is None. Not used by GMROTD.
        """
        super().__init__(imc, imt, percentile=None, period=None)
        self.percentile = percentile
        self._steps = {
                'Rotation': 'gmrotd',
                'Combination2': 'null_combination',
                'Reduction': 'percentile'
        }
        self._invalid_imts = ['FAS', 'ARIAS']
