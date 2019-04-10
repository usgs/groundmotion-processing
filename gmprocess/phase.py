# stdlib imports
import datetime as dt
import logging

# third party imports
import numpy as np
from scipy.signal import butter, lfilter, hilbert
import scipy.linalg as alg
from obspy.signal.trigger import ar_pick, pk_baer

# local imports
from gmprocess.exception import GMProcessException
from gmprocess.config import get_config


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


# Adapted from MATLAB script
def AICPicker(data, triggers, search_window, sps):

    refined_triggers = []
    data = data - np.median(data)
    searchwindowpts = int(sps * search_window)

    for trigpts in triggers:

        trigstart = (trigpts - (2 * searchwindowpts))
        trigend = trigpts + 1 * searchwindowpts

        if(trigstart > 0 and trigend < np.size(data)):
            data_select = data[trigstart:trigend]
        else:
            continue

        data_select_size = np.size(data_select)
        pts_select = np.arange(data_select_size) - 2 * searchwindowpts

        AIC = np.zeros(np.size(data_select))

        for n in range(1, np.size(AIC) - 2):
            s1 = np.var(data_select[0:n])
            if(s1 <= 0):
                s1 = 0
            else:
                s1 = np.log(s1)
            s2 = np.var(data_select[(n + 1):-1])
            if(s2 <= 0):
                s2 = 0
            else:
                s2 = np.log(s2)
            AIC[n] = (n * s1) + ((np.size(AIC) - n + 1) * s2)

        AIC[0:5] = np.inf
        AIC[-5:] = np.inf

        refined_triggers.append(pts_select[np.argmin(AIC) + 1] + trigpts)

    return refined_triggers


def STALTA_Earle(data, datao, sps, STAW, STAW2, LTAW, hanning, threshold,
                 threshold2, threshdrop):
    data_hil = hilbert(data)
    envelope = np.abs(data_hil)
    envelope = np.convolve(envelope, np.hanning(hanning * sps), mode='same')

    sta_samples = int(STAW * sps)
    sta_samples2 = int(STAW2 * sps)
    lta_samples = int(LTAW * sps)

    sta = np.zeros(np.size(envelope))
    sta2 = np.zeros(np.size(envelope))
    lta = np.zeros(np.size(envelope))

    for i in range(np.size(envelope) - lta_samples - 1):
        lta[i + lta_samples + 1] = np.sum(envelope[i:i + lta_samples])
        sta[i + lta_samples + 1] = np.sum(envelope[i + lta_samples + 1:i
                                                   + lta_samples + sta_samples + 1])
        sta2[i + lta_samples + 1] = np.sum(envelope[i + lta_samples + 1:i
                                                    + lta_samples + 1
                                                    + sta_samples2])

    lta = lta / float(lta_samples)
    sta = sta / float(sta_samples)
    sta2 = sta2 / float(sta_samples2)

    lta[lta < 0.00001] = 0.00001

    ratio = sta / lta
    ratio2 = sta2 / lta

    trigger = False
    triggers_on = []
    triggers_off = []

    for i in range(np.size(ratio) - 1):
        if(trigger is False and ratio[i] >= threshold
           and ratio2[i] >= threshold2 and ratio[i] > ratio[i + 1]):
            triggers_on.append(i)
            trigger = True
        elif(trigger is True and ratio[i] <= threshdrop):
            triggers_off.append(i)
            trigger = False

    refined_triggers = AICPicker(data, triggers_on, 4., sps)

    return (refined_triggers, triggers_on, triggers_off, ratio, ratio2,
            envelope, sta, lta)


def PowerPicker(tr, highpass=1.4, lowpass=6, order=3, sta=3.0, sta2=3.0,
                lta=20.0, hanningWindow=3.0, threshDetect=2.0,
                threshDetect2=2.5, threshRestart=99999999):
    """Pick P-wave arrival time.

    Args:
        tr (StationTrace):
            StationTrace containing waveform to be picked.
        highpass (float):
            Frequency of the high-pass filter.
        lowpass (float):
            Frequency of the low-pass filter.
        order (int):
            Order of the filter.
        sta (float):
            First short term average window (s).
        sta2 (float):
            Second short term average window (s).
        lta (float):
            Long term average window (s).
        hanningWindow (float):
            length of the Hanning window in seconds applied to the
            characteristic function.
        threshDetect (float):
            First detection threshold.
        threshDetect2 (float):
            Second detection threshold.
        threshRestart (float):
            threshRestart is the threshold where the picker rearms to choose
            another pick.

    Returns:
        float:
            P-wave pick time as number of seconds after start of trace.
    """
    tr_copy = tr.copy()
    tr_copy.resample(20)
    tr_copy.detrend()
    data = tr_copy.data
    sps = tr_copy.stats.sampling_rate

    datahigh = butter_bandpass_filter(data, highpass, lowpass, sps,
                                      order=order)

    rt = STALTA_Earle(datahigh, data, sps, sta, sta2, lta, hanningWindow,
                      threshDetect, threshDetect2, threshRestart)[0]

    if not len(rt):
        return -1
    rt2 = dt.timedelta(seconds=(rt[0] / sps)).total_seconds()
    return rt2


def pick_kalkan(stream, picker_config=None, config=None):
    """Wrapper around the Kalkan P-phase picker.

    Args:
        stream (StationStream):
            Stream containing waveforms that need to be picked.
        picker_config (dict):
            Dictionary with parameters for Kalkan P-phase picker. See picker.yml.
        config (dict):
            Configuration dictionary. Key value here is:
                windows:
                    window_checks:
                        min_noise_duration
    Returns:
        tuple: 
            - Best estimate for p-wave arrival time (s since start of trace).
            - Mean signal to noise ratio based on the pick.
    """
    if picker_config is None:
        picker_config = get_config(picker=True)
    if config is None:
        config = get_config()
    min_noise_dur = config['windows']['window_checks']['min_noise_duration']
    params = picker_config['kalkan']
    locs = []
    for trace in stream:
        loc = pphase_pick(trace, **params)
        if loc >= 0:
            locs.append(loc)
    locs = np.array(locs)
    if np.any(locs >= 0):
        minloc = np.min(locs[locs >= 0])
    else:
        minloc = -1
    if minloc < min_noise_dur:
        fmt = 'Noise window (%.1f s) less than minimum (%.1f)'
        tpl = (minloc, min_noise_dur)
        raise GMProcessException(fmt % tpl)
    mean_snr = calc_snr(stream, minloc)

    return (minloc, mean_snr)


def pick_ar(stream, picker_config=None, config=None):
    """Wrapper around the AR P-phase picker.

    Args:
        stream (StationStream):
            Stream containing waveforms that need to be picked.
        picker_config (dict):
            Dictionary with parameters for AR P-phase picker. See picker.yml.
        config (dict):
            Configuration dictionary. Key value here is:
                windows:
                    window_checks:
                        min_noise_duration
    Returns:
        tuple: 
            - Best estimate for p-wave arrival time (s since start of trace).
            - Mean signal to noise ratio based on the pick.
    """
    if picker_config is None:
        picker_config = get_config(picker=True)
    if config is None:
        config = get_config()
    min_noise_dur = config['windows']['window_checks']['min_noise_duration']
    params = picker_config['ar']
    # Get the east, north, and vertical components from the stream
    st_e = stream.select(channel='??[E1]')
    st_n = stream.select(channel='??[N2]')
    st_z = stream.select(channel='??[Z3]')

    # Check if we found one of each component
    # If not, use the next picker in the order of preference
    if len(st_e) != 1 or len(st_n) != 1 or len(st_z) != 1:
        raise GMProcessException('Unable to perform AR picker.')

    minloc = ar_pick(st_z[0].data, st_n[0].data, st_e[0].data,
                     st_z[0].stats.sampling_rate,
                     **params)[0]
    if minloc < min_noise_dur:
        fmt = 'Noise window (%.1f s) less than minimum (%.1f)'
        tpl = (minloc, min_noise_dur)
        raise GMProcessException(fmt % tpl)
    mean_snr = calc_snr(stream, minloc)

    return (minloc, mean_snr)


def pick_baer(stream, picker_config=None, config=None):
    """Wrapper around the Baer P-phase picker.

    Args:
        stream (StationStream):
            Stream containing waveforms that need to be picked.
        picker_config (dict):
            Dictionary with parameters for Baer P-phase picker. See picker.yml.
        config (dict):
            Configuration dictionary. Key value here is:
                windows:
                    window_checks:
                        min_noise_duration
    Returns:
        tuple: 
            - Best estimate for p-wave arrival time (s since start of trace).
            - Mean signal to noise ratio based on the pick.
    """
    if picker_config is None:
        picker_config = get_config(picker=True)
    if config is None:
        config = get_config()
    min_noise_dur = config['windows']['window_checks']['min_noise_duration']
    params = picker_config['baer']
    locs = []
    for trace in stream:
        pick_sample = pk_baer(trace.data, trace.stats.sampling_rate,
                              **params)[0]
        loc = pick_sample * trace.stats.delta
        locs.append(loc)

    locs = np.array(locs)
    if np.any(locs >= 0):
        minloc = np.min(locs[locs >= 0])
    else:
        minloc = -1
    if minloc < min_noise_dur:
        fmt = 'Noise window (%.1f s) less than minimum (%.1f)'
        tpl = (minloc, min_noise_dur)
        raise GMProcessException(fmt % tpl)
    mean_snr = calc_snr(stream, minloc)

    return (minloc, mean_snr)


def pick_yeck(stream):
    """IN DEVELOPMENT! SNR based P-phase picker.

    Args:
        stream (StationStream):
            Stream containing waveforms that need to be picked.
    Returns:
        tuple: 
            - Best estimate for p-wave arrival time (s since start of trace).
            - Mean signal to noise ratio based on the pick.
    """
    min_window = 5.0  # put into config
    config = get_config()
    min_noise_dur = config['windows']['window_checks']['min_noise_duration']
    locs = []
    for trace in stream:
        data = trace.data
        sr = trace.stats.sampling_rate
        pidx_start = int(min_window * sr)
        snr = np.zeros(len(data))
        for pidx in range(pidx_start, len(data) - pidx_start):
            snr_i = sub_calc_snr(data, pidx)
            snr[pidx] = snr_i
        snr = np.array(snr)
        pidx = snr.argmax()
        loc = pidx / sr
        locs.append(loc)

    locs = np.array(locs)
    if np.any(locs >= 0):
        minloc = np.min(locs[locs >= 0])
    else:
        minloc = -1
    if minloc < min_noise_dur:
        fmt = 'Noise window (%.1f s) less than minimum (%.1f)'
        tpl = (minloc, min_noise_dur)
        raise GMProcessException(fmt % tpl)
    mean_snr = calc_snr(stream, minloc)

    return (minloc, mean_snr)


def pick_power(stream, picker_config=None, config=None):
    """Wrapper around the PowerPicker.

    Args:
        stream (StationStream):
            Stream containing waveforms that need to be picked.
        picker_config (dict):
            Dictionary with parameters for PowerPicker. See picker.yml.
        config (dict):
            Configuration dictionary. Key value here is:
                windows:
                    window_checks:
                        min_noise_duration
    Returns:
        tuple: 
            - Best estimate for p-wave arrival time (s since start of trace).
            - Mean signal to noise ratio based on the pick.
    """
    if picker_config is None:
        picker_config = get_config(picker=True)
    if config is None:
        config = get_config()
    min_noise_dur = config['windows']['window_checks']['min_noise_duration']
    params = picker_config['power']
    locs = []
    for trace in stream:
        loc = PowerPicker(trace, **params)
        locs.append(loc)

    locs = np.array(locs)
    if np.any(locs >= 0):
        minloc = np.min(locs[locs >= 0])
    else:
        minloc = -1
    if minloc < min_noise_dur:
        fmt = 'Noise window (%.1f s) less than minimum (%.1f)'
        tpl = (minloc, min_noise_dur)
        raise GMProcessException(fmt % tpl)
    mean_snr = calc_snr(stream, minloc)

    return (minloc, mean_snr)


def calc_snr2(stream, loc):
    snr_values = []
    for trace in stream:
        data = trace.data
        pidx = int(loc * trace.stats.sampling_rate)
        snr_i = sub_calc_snr(data, pidx)
        snr_values.append(snr_i)

    mean_snr = np.mean(snr_values)
    return mean_snr


def sub_calc_snr(data, pidx):
    signal = data[pidx:]
    noise = data[0:pidx]
    aps = np.mean(np.power(signal, 2))  # average power of signal
    apn = np.mean(np.power(noise, 2))   # average power of noise
    aps /= len(signal)
    apn /= len(noise)
    if apn == 0:
        apn = 0.00001
    if aps == 0:
        aps = 0.00001
    # signal-to-noise ratio in decibel
    try:
        snr = 10 * np.math.log10(aps / apn)
    except ValueError as ve:
        raise(ve)

    return snr


def calc_snr(stream, minloc):
    """Calculate mean SNR for all Traces in a StationStream.

    Args:
        stream (StationStream):
            Stream containing waveforms.
        minloc (float):
            Time in seconds since beginning of Trace.

    Returns:
        float:
            Ratio of signal window (minloc->end of trace) over 
            noise window (start of trace->minloc)

    """
    snr_values = []
    for trace in stream:
        dt = trace.stats.delta
        signal = trace.data
        noise = trace.data[0:int(minloc / dt)]
        aps = np.mean(np.power(signal, 2))  # average power of signal
        apn = np.mean(np.power(noise, 2))   # average power of noise
        if apn == 0:
            apn = 0.00001
            logging.warning(
                'Noise window for %s has mean of zero.' % trace.get_id())
        # signal-to-noise ratio in decibel
        snr_i = 10 * np.math.log10(aps / apn)
        snr_values.append(snr_i)

    return np.mean(snr_values)


def pphase_pick(trace, period=None, damping=0.6, nbins=None,
                peak_selection=False):
    """Compute P-phase arrival time.

    Adapted from Python code written by Francisco Hernandez of the Puerto Rico
    Strong Motion Program.

    That code was in turn adapted from Matlab code written by Dr. Erol
    Kalkan, P.E.

    The algorithms are described here in full:

    Kalkan, E. (2016). "An automatic P-phase arrival time picker", Bull. of
    Seismol. Soc. of Am., 106, No. 3, doi: 10.1785/0120150111

    Args:
        trace (StationTrace):
            StationTrace containing waveform (acceleration or velocity) data.
        period (float):
            Undamped natural period of the sensor in seconds.
            Defaults to 0.01s for sample rates >= 100, 0.1s for sample rates < 100.
        damping (float):
            Damping ratio.
        nbins (int):
            Histogram bin size (default is 2/sampling interval). Regional or
            teleseismic records may need different values of bin size for
            better picking results)
        selection (Selector):
            One of:
                Selector.TO_PEAK - take segment of waveform from beginning to
                    absolute peak value (recommended for fast processing).
                Selector.FULL - take full waveform.
    Returns:
        tuple:
            - Float number of seconds from start of trace to P-Phase beginning.
            - Signal-to-noise ratio in decibels
    """
    WAVEFORM_TYPES = {'acc': 'sm', 'vel': 'wm'}
    wftype = WAVEFORM_TYPES[trace.stats.standard['units']]
    if period == 'None':
        if trace.stats.sampling_rate >= 100:
            period = 0.01
        else:
            period = 0.1

    if nbins == 'None':
        nbins = 2 / trace.stats.delta

    if wftype == 'wm':
        filtflag = 1
        flp = 0.1
        fhp = 10.0
    else:
        # Strong-motion low- and high-pass corner frequencies in Hz
        filtflag = 1
        flp = 0.1
        fhp = 20.0

    trace_copy = trace.copy()
    dt = trace_copy.stats.delta

    # Normalize input to prevent numerical instability from very low amplitudes
    trace_copy.data = trace_copy.data / np.max(np.abs(trace_copy.data))

    if filtflag is not 0:
        trace_copy.filter(type='bandpass', freqmin=flp, freqmax=fhp,
                          corners=4, zerophase=True)
        trace_copy.detrend(type='linear')

    if peak_selection == 'True':
        ind_peak = np.nonzero(np.abs(trace_copy.data)
                              == np.max(np.abs(trace_copy.data)))
        trace_copy.data = trace_copy.data[0:ind_peak[0][0]]

    # Construct a fixed-base viscously damped SDF oscillator
    omegan = 2 * np.pi / period           # natural frequency in radian/second
    C = 2 * damping * omegan               # viscous damping term
    K = omegan**2                 # stiffness term
    y = np.zeros((2, len(trace_copy.data)))   # response vector

    # Solve second-order ordinary differential equation of motion
    A = np.array([[0, 1], [-K, -C]])
    Ae = alg.expm(A * dt)
    AeB = np.dot(alg.lstsq(A, (Ae - np.identity(2)))[0], np.array((0, 1)))

    for k in range(1, len(trace_copy.data)):
        y[:, k] = np.dot(Ae, y[:, k - 1]) + AeB * trace_copy.data[k]

    # relative velocity of mass
    veloc = (y[1, :])
    # integrand of viscous damping energy
    Edi = np.dot(2 * damping * omegan, np.power(veloc, 2))

    # Apply histogram method
    levels, histogram, bins = _get_statelevel(Edi, nbins)
    locs = np.nonzero(Edi > levels[0])[0]
    # get zero crossings
    indx = np.nonzero(np.multiply(trace_copy.data[0:locs[0] - 1],
                                  trace_copy.data[1:locs[0]]) < 0)[0]
    TF = indx.size

    # Update first onset
    if TF is not 0:
        loc = (indx[TF - 1] + 1) * dt
    else:
        # try nbins/2
        levels, histogram, bins = _get_statelevel(Edi, np.ceil(nbins / 2))
        locs = np.nonzero(Edi > levels[0])[0]
        # get zero crossings
        indx = np.nonzero(np.multiply(trace_copy.data[0:locs[0] - 1],
                                      trace_copy.data[1:locs[0]]) < 0)[0]
        TF = indx.size
        if TF is not 0:
            loc = (indx[TF - 1] + 1) * dt
        else:
            loc = -1

    return loc


def _get_statelevel(y, n):
    ymax = np.amax(y)
    ymin = np.min(y) - np.finfo(float).eps

    # Compute Histogram
    idx = np.ceil(n * (y - ymin) / (ymax - ymin))
    condition = np.logical_and(idx >= 1, idx <= n)
    idx = np.extract(condition, idx)
    s = (int(n), 1)
    histogram = np.zeros(s)
    for i in range(1, np.size(idx)):
        histogram[int(idx[i]) - 1] = histogram[int(idx[i]) - 1] + 1

    # Compute Center of Each Bin
    ymin = np.min(y)
    Ry = ymax - ymin
    dy = Ry / n
    bins = ymin + (np.arange(1, n) - 0.5) * dy

    # Compute State Levels
    nz = np.nonzero(histogram)[0]  # indices
    iLowerRegion = nz[0]
    iUpperRegion = nz[np.size(nz) - 1]

    iLow = iLowerRegion
    iHigh = iUpperRegion

    # Define the lower and upper histogram regions halfway
    # between the lowest and highest nonzero bins.
    lLow = iLow
    lHigh = iLow + np.floor((iHigh - iLow) / 2)
    uLow = iLow + np.floor((iHigh - iLow) / 2)
    uHigh = iHigh

    # Upper and lower histograms
    lHist = histogram[int(lLow):int(lHigh)]
    uHist = histogram[int(uLow):int(uHigh)]

    levels = np.zeros(2)
    iMax = np.argmax(lHist[1, :])
    iMin = np.argmax(uHist)
    levels[0] = ymin + dy * (lLow + iMax + 0.5)
    levels[1] = ymin + dy * (uLow + iMin + 0.5)

    # Lowest histogram bin numbers for upper and lower histograms
    # lHist_final = (lLow + iMax);
    # uHist_final = (uLow + iMin);
    return levels, histogram, bins
