

import numpy as np

from gmprocess.smoothing.konno_ohmachi import konno_ohmachi_smooth


def fft_smooth(trace, nfft):
    """
    Pads a trace to the nearest upper power of 2, takes the FFT, and
    smooths the amplitude spectra following the algorithm of
    Konno and Ohmachi.

    Args:
        trace (obspy.core.trace.Trace): Trace of strong motion data.
        nfft (int): Number of data points for the fourier transform.

    Returns:
        numpy.ndarray: Smoothed amplitude data and frequencies.
    """

    # Compute the FFT, normalizing by the number of data points
    spec = abs(np.fft.rfft(trace.data, n=nfft)) / nfft

    # Get the frequencies associated with the FFT
    freqs = np.fft.rfftfreq(nfft, 1 / trace.stats.sampling_rate)
    # Do a maximum of 301 K-O frequencies in the range of the fft freqs
    nkofreqs = min(nfft, 302) - 1
    ko_freqs = np.logspace(np.log10(freqs[1]), np.log10(freqs[-1]), nkofreqs)
    # An array to hold the output
    spec_smooth = np.empty_like(ko_freqs)

    # Konno Omachi Smoothing using 20 for bandwidth parameter
    konno_ohmachi_smooth(spec.astype(np.double), freqs, ko_freqs, spec_smooth,
                         20.0)
    return spec_smooth, ko_freqs
