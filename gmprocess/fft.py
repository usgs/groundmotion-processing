

import numpy as np

from gmprocess.smoothing.konno_ohmachi import konno_ohmachi_smooth


def fft_smooth(trace, nfft, bandwidth=20):
    """
    Pads a trace to the nearest upper power of 2, takes the FFT, and
    smooths the amplitude spectra following the algorithm of
    Konno and Ohmachi.

    Args:
        trace (StationTrace):
            Trace of strong motion data.
        nfft (int):
            Number of data points for the fourier transform.
        bandwidth (float):
            Konno-Omachi smoothing bandwidth parameter.

    Returns:
        numpy.ndarray: Smoothed amplitude data and frequencies.
    """

    # Compute the FFT, normalizing by the number of data points
    dt = trace.stats.delta
    spec = abs(np.fft.rfft(trace.data, n=nfft)) * dt

    # Get the frequencies associated with the FFT
    freqs = np.fft.rfftfreq(nfft, dt)

    # Do a maximum of 301 K-O frequencies in the range of the fft freqs
    nkofreqs = min(nfft, 302) - 1
    ko_freqs = np.logspace(np.log10(freqs[1]), np.log10(freqs[-1]), nkofreqs)
    # An array to hold the output
    spec_smooth = np.empty_like(ko_freqs)

    # Konno Omachi Smoothing
    konno_ohmachi_smooth(
        spec.astype(np.double), freqs, ko_freqs, spec_smooth, bandwidth)
    return spec_smooth, ko_freqs
