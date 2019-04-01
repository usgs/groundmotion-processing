
import numpy as np

from obspy.signal.util import next_pow_2

from gmprocess.fft import fft_smooth


# Options for tapering noise/signal windows
TAPER_WIDTH = 0.05
TAPER_TYPE = 'hann'
TAPER_SIDE = 'both'
MIN_POINTS_IN_WINDOW = 10


def compute_snr(tr, bandwidth):
    """Compute SNR dictionaries for a trace.

    Args:
        tr (StationTrace):
           Trace of data.
        bandwidth (float):
           Konno-Omachi smoothing bandwidth parameter.

    Returns:
        StationTrace with SNR dictionaries added as trace parameters.
    """
    # Split the noise and signal into two separate traces
    split_prov = tr.getParameter('signal_split')
    if isinstance(split_prov, list):
        split_prov = split_prov[0]
    split_time = split_prov['split_time']
    noise = tr.copy().trim(endtime=split_time)
    signal = tr.copy().trim(starttime=split_time)

    # Taper both windows
    noise.taper(max_percentage=TAPER_WIDTH,
                type=TAPER_TYPE,
                side=TAPER_SIDE)
    signal.taper(max_percentage=TAPER_WIDTH,
                 type=TAPER_TYPE,
                 side=TAPER_SIDE)

    # Need values in both noise and signal windows
    if noise.stats.npts < MIN_POINTS_IN_WINDOW:
        tr.fail('Failed SNR check; Not enough points in noise window.')
        return tr
    if signal.stats.npts < MIN_POINTS_IN_WINDOW:
        tr.fail('Failed SNR check; Not enough points in signal window.')
        return tr

    nfft = max(next_pow_2(signal.stats.npts),
               next_pow_2(noise.stats.npts))

    # Transform to frequency domain and smooth spectra using
    # konno-ohmachi smoothing
    dt = signal.stats.delta
    sig_spec = abs(np.fft.rfft(signal.data, n=nfft)) * dt
    sig_spec_freqs = np.fft.rfftfreq(nfft, dt)
    dt = noise.stats.delta
    noise_spec = abs(np.fft.rfft(noise.data, n=nfft)) * dt
    sig_spec -= noise_spec

    sig_dict = {
        'spec': sig_spec.tolist(),
        'freq': sig_spec_freqs.tolist()
    }
    tr.setParameter('signal_spectrum', sig_dict)

    noise_dict = {
        'spec': noise_spec.tolist(),
        'freq': sig_spec_freqs.tolist()  # same as signal
    }
    tr.setParameter('noise_spectrum', noise_dict)

    sig_spec_smooth, freqs_signal = fft_smooth(
        signal, nfft, bandwidth)
    smooth_dict = {
        'spec': sig_spec_smooth.tolist(),
        'freq': freqs_signal.tolist()
    }
    tr.setParameter('smooth_signal_spectrum', smooth_dict)

    noise_spec_smooth, freqs_noise = fft_smooth(noise, nfft)
    noise_smooth_dict = {
        'spec': noise_spec_smooth.tolist(),
        'freq': freqs_noise.tolist()
    }
    tr.setParameter('smooth_noise_spectrum', noise_smooth_dict)

    # remove the noise level from the spectrum of the signal window
    sig_spec_smooth -= noise_spec_smooth

    snr = sig_spec_smooth/noise_spec_smooth
    snr_dict = {
        'snr': snr.tolist(),
        'freq': freqs_signal.tolist()
    }
    tr.setParameter('snr', snr_dict)
    return tr
