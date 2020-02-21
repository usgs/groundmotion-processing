# Third party imports
import numpy as np

# Local imports
from gmprocess.metrics.transform.transform import Transform
from gmprocess.fft import compute_fft


class FFT(Transform):
    """Class for computing the fast fourier transform."""
    def __init__(self, transform_data, damping=None, period=None, times=None):
        """
        Args:
            transform_data (obspy.core.stream.Stream or numpy.ndarray): Intensity
                    measurement component.
            damping (float): Damping for spectral amplitude calculations.
                    Default is None.
            period (float): Period for spectral amplitude calculations.
                    Default is None.
            times (numpy.ndarray): Times for the spectral amplitude calculations.
                    Default is None.
        """
        super().__init__(transform_data, damping=None, period=None, times=None)
        self.result = self.get_fft()

    def get_fft(self):
        """
        Calculated the fft of each trace's data.

        Returns:
            numpy.ndarray: Computed fourier amplitudes.
        """
        horizontals = self._get_horizontals()
        nfft = len(horizontals[0].data)
        sampling_rate = horizontals[0].stats.sampling_rate
        freqs = np.fft.rfftfreq(nfft, 1 / sampling_rate)
        ft_traces = [freqs]

        # Check if we already have computed the FFT for this trace
        for trace in horizontals:
            if trace.hasCached('fas_spectrum'):
                spectra = trace.getCached('fas_spectrum')
            else:
                # the fft scales so the factor of 1/nfft is applied
                spectra, freqs = compute_fft(trace, nfft)
                trace.setCached('fas_spectrum', spectra)

            ft_traces += [spectra]

        return ft_traces
