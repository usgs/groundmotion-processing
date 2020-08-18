# Third party imports
import numpy as np

# Local imports
from gmprocess.metrics.transform.transform import Transform
from gmprocess.fft import compute_fft


class FFT(Transform):
    """Class for computing the fast fourier transform.
    """

    def __init__(self, transform_data, damping=None, period=None, times=None,
                 max_period=None):
        """
        Args:
            transform_data (obspy.core.stream.Stream or numpy.ndarray):
                Intensity measurement component.
            damping (float):
                Damping for spectral amplitude calculations. Default is None.
            period (float):
                Period for spectral amplitude calculations. Default is None.
            times (numpy.ndarray):
                Times for the spectral amplitude calculations. Default is None.
        """
        super().__init__(transform_data, damping=None, period=None, times=None,
                         max_period=None)
        self.result = self.get_fft()

    def get_fft(self):
        """
        Calculated the fft of each trace's data.

        Returns:
            numpy.ndarray: Computed fourier amplitudes.
        """
        fft_dict = {}
        for trace in self.transform_data:

            # Check if we already have computed the FFT for this trace
            if trace.hasCached('fas_spectrum'):
                spectra = trace.getCached('fas_spectrum')
                sampling_rate = trace.stats.sampling_rate
                freqs = np.fft.rfftfreq(nfft, 1 / sampling_rate)
            else:
                spectra, freqs = compute_fft(trace, nfft)
                trace.setCached('fas_spectrum', spectra)

            tdict = {
                'freqs': freqs,
                'spectra': spectra
            }
            fft_dict[trace.stats['channel'].upper()] = tdict

        return fft_dict

    def get_nfft(self):
        
