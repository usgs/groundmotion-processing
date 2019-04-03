
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
    # Do we have estimates of the signal split time?
    if tr.hasParameter('signal_split'):
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

        # Check that there are a minimum number of points in the noise window
        if noise.stats.npts < MIN_POINTS_IN_WINDOW:
            # Fail the trace, but still compute the signal spectra
            # ** only fail here if it hasn't already failed; we do not yet
            # ** support tracking multiple fail reasons and I think it is
            # ** better to know the FIRST reason if I have to pick one.
            if not tr.hasParameter('failure'):
                tr.fail('Failed SNR check; Not enough points in noise window.')
            tr = compute_signal_spectrum(tr, bandwidth)
            return tr

        # Check that there are a minimum number of points in the noise window
        if signal.stats.npts < MIN_POINTS_IN_WINDOW:
            # Fail the trace, but still compute the signal spectra
            if not tr.hasParameter('failure'):
                tr.fail(
                    'Failed SNR check; Not enough points in signal window.')
            tr = compute_signal_spectrum(tr, bandwidth)
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
    else:
        # We do not have an estimate of the signal split time for this trace
        tr = compute_signal_spectrum(tr, bandwidth)
    return tr


def compute_signal_spectrum(tr, bandwidth):
    """
    Compute raw and smoothed signal spectrum.

    Args:
        tr (StationTrace):
           Trace of data.
        bandwidth (float):
           Konno-Omachi smoothing bandwidth parameter.

    Returns:
        StationTrace with signal spectrum dictionaries added as trace
        parameters.

    """
    # Transform to frequency domain and smooth spectra using
    # konno-ohmachi smoothing
    nfft = next_pow_2(tr.stats.npts)

    dt = tr.stats.delta
    sig_spec = abs(np.fft.rfft(tr.data, n=nfft)) * dt
    sig_spec_freqs = np.fft.rfftfreq(nfft, dt)

    sig_dict = {
        'spec': sig_spec.tolist(),
        'freq': sig_spec_freqs.tolist()
    }
    tr.setParameter('signal_spectrum', sig_dict)
    return tr
