# Local import
from gmprocess.metrics.oscillators import get_spectral
from gmprocess.metrics.transform.transform import Transform


class oscillator(Transform):
    """Class for computing the oscillator for a given period."""
    def __init__(self, transform_data, damping, period, times):
        """
        Args:
            transform_data (obspy.core.stream.Stream or numpy.ndarray): Intensity
                    measurement component.
            damping (float): Damping for spectral amplitude calculations.
            period (float): Period for spectral amplitude calculations.
            times (numpy.ndarray): Times for the spectral amplitude calculations.
        """
        super().__init__(transform_data, damping=None, period=None, times=None)
        self.period = period
        self.damping = damping
        self.times = times
        self.result = self.get_oscillator()

    def get_oscillator(self):
        """
        Calculated the oscillator of each trace's data.

        Returns:
            spectrals: StationStream or numpy.ndarray with the
                    differentiated data.
        """
        spectrals = get_spectral(self.period,
                self.transform_data, damping=self.damping, times=self.times)
        return spectrals
