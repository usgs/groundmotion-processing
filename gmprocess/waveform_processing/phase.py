#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import datetime as dt
import logging

# third party imports
import numpy as np
import pandas as pd
from scipy.signal import butter, lfilter, hilbert
from scipy.interpolate import griddata
import scipy.linalg as alg
from obspy.signal.trigger import ar_pick, pk_baer
from obspy.core.utcdatetime import UTCDateTime
from obspy.geodetics.base import locations2degrees
from obspy.taup import TauPyModel

# local imports
from gmprocess.utils.config import get_config
from gmprocess.utils.event import ScalarEvent

NAN_TIME = UTCDateTime("1970-01-01T00:00:00")

CONFIG = get_config()


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype="band")
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

        trigstart = trigpts - (2 * searchwindowpts)
        trigend = trigpts + 1 * searchwindowpts

        if trigstart > 0 and trigend < np.size(data):
            data_select = data[trigstart:trigend]
        else:
            continue

        data_select_size = np.size(data_select)
        pts_select = np.arange(data_select_size) - 2 * searchwindowpts

        AIC = np.zeros(np.size(data_select))

        for n in range(1, np.size(AIC) - 2):
            s1 = np.var(data_select[0:n])
            if s1 <= 0:
                s1 = 0
            else:
                s1 = np.log(s1)
            s2 = np.var(data_select[(n + 1) : -1])
            if s2 <= 0:
                s2 = 0
            else:
                s2 = np.log(s2)
            AIC[n] = (n * s1) + ((np.size(AIC) - n + 1) * s2)

        AIC[0:5] = np.inf
        AIC[-5:] = np.inf

        refined_triggers.append(pts_select[np.argmin(AIC) + 1] + trigpts)

    return refined_triggers


def STALTA_Earle(
    data, datao, sps, STAW, STAW2, LTAW, hanning, threshold, threshold2, threshdrop
):
    data_hil = hilbert(data)
    envelope = np.abs(data_hil)
    envelope = np.convolve(envelope, np.hanning(hanning * sps), mode="same")

    sta_samples = int(STAW * sps)
    sta_samples2 = int(STAW2 * sps)
    lta_samples = int(LTAW * sps)

    sta = np.zeros(np.size(envelope))
    sta2 = np.zeros(np.size(envelope))
    lta = np.zeros(np.size(envelope))

    for i in range(np.size(envelope) - lta_samples - 1):
        lta[i + lta_samples + 1] = np.sum(envelope[i : i + lta_samples])
        sta[i + lta_samples + 1] = np.sum(
            envelope[i + lta_samples + 1 : i + lta_samples + sta_samples + 1]
        )
        sta2[i + lta_samples + 1] = np.sum(
            envelope[i + lta_samples + 1 : i + lta_samples + 1 + sta_samples2]
        )

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
        if (
            (not trigger)
            and ratio[i] >= threshold
            and ratio2[i] >= threshold2
            and ratio[i] > ratio[i + 1]
        ):
            triggers_on.append(i)
            trigger = True
        elif trigger and (ratio[i] <= threshdrop):
            triggers_off.append(i)
            trigger = False

    refined_triggers = AICPicker(data, triggers_on, 4.0, sps)

    return (
        refined_triggers,
        triggers_on,
        triggers_off,
        ratio,
        ratio2,
        envelope,
        sta,
        lta,
    )


def PowerPicker(
    tr,
    highpass=1.4,
    lowpass=6,
    order=3,
    sta=3.0,
    sta2=3.0,
    lta=20.0,
    hanningWindow=3.0,
    threshDetect=2.0,
    threshDetect2=2.5,
    threshRestart=99999999,
):
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
    tr_copy.resample(20, window='hann')
    tr_copy.detrend()
    data = tr_copy.data
    sps = tr_copy.stats.sampling_rate

    datahigh = butter_bandpass_filter(data, highpass, lowpass, sps, order=order)

    rt = STALTA_Earle(
        datahigh,
        data,
        sps,
        sta,
        sta2,
        lta,
        hanningWindow,
        threshDetect,
        threshDetect2,
        threshRestart,
    )[0]

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
            Dictionary with parameters for Kalkan P-phase picker.
            See picker.yml.
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
        picker_config = CONFIG["pickers"]
    min_noise_dur = CONFIG["windows"]["window_checks"]["min_noise_duration"]
    params = picker_config["kalkan"]
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
        fmt = "Noise window (%.1f s) less than minimum (%.1f)"
        tpl = (minloc, min_noise_dur)
        raise ValueError(fmt % tpl)
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
        picker_config = CONFIG["pickers"]
    min_noise_dur = CONFIG["windows"]["window_checks"]["min_noise_duration"]
    params = picker_config["ar"]
    # Get the east, north, and vertical components from the stream
    st_e = stream.select(channel="??[E1]")
    st_n = stream.select(channel="??[N2]")
    st_z = stream.select(channel="??[Z3]")

    # Check if we found one of each component
    # If not, use the next picker in the order of preference
    if len(st_e) != 1 or len(st_n) != 1 or len(st_z) != 1:
        raise BaseException("Unable to perform AR picker.")

    minloc = ar_pick(
        st_z[0].data, st_n[0].data, st_e[0].data, st_z[0].stats.sampling_rate, **params
    )[0]
    if minloc < min_noise_dur:
        fmt = "Noise window (%.1f s) less than minimum (%.1f)"
        tpl = (minloc, min_noise_dur)
        raise ValueError(fmt % tpl)
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
        picker_config = CONFIG["pickers"]
    min_noise_dur = CONFIG["windows"]["window_checks"]["min_noise_duration"]
    params = picker_config["baer"]
    locs = []
    for trace in stream:
        pick_sample = pk_baer(trace.data, trace.stats.sampling_rate, **params)[0]
        loc = pick_sample * trace.stats.delta
        locs.append(loc)

    locs = np.array(locs)
    if np.any(locs >= 0):
        minloc = np.min(locs[locs >= 0])
    else:
        minloc = -1
    if minloc < min_noise_dur:
        fmt = "Noise window (%.1f s) less than minimum (%.1f)"
        tpl = (minloc, min_noise_dur)
        raise ValueError(fmt % tpl)
    mean_snr = calc_snr(stream, minloc)

    return (minloc, mean_snr)


def pick_travel(stream, origin, model=None, picker_config=None):
    """Use TauP travel time model to find P-Phase arrival time.

    Args:
        stream (StationStream):
            StationStream containing 1 or more channels of waveforms.
        origin (ScalarEvent):
            Event origin/magnitude information.
        model (TauPyModel):
            TauPyModel object for computing travel times.
    Returns:
        tuple:
            - Best estimate for p-wave arrival time (s since start of trace).
            - Mean signal to noise ratio based on the pick.
    """
    if model is None:
        if picker_config is None:
            picker_config = CONFIG["pickers"]
        model = TauPyModel(picker_config["travel_time"]["model"])
    if stream[0].stats.starttime == NAN_TIME:
        return (-1, 0)
    lat = origin.latitude
    lon = origin.longitude
    depth = origin.depth_km
    if depth < 0:
        depth = 0
    etime = origin.time
    slat = stream[0].stats.coordinates.latitude
    slon = stream[0].stats.coordinates.longitude

    dist_deg = locations2degrees(lat, lon, slat, slon)
    try:
        arrivals = model.get_travel_times(
            source_depth_in_km=depth,
            distance_in_degree=dist_deg,
            phase_list=["P", "p", "Pn"],
        )
    except BaseException as e:
        fmt = 'Exception "%s" generated by get_travel_times() ' "dist=%.3f depth=%.1f"
        logging.warning(fmt % (str(e), dist_deg, depth))
        arrivals = []
    if not len(arrivals):
        return (-1, 0)

    # arrival time is time since origin
    arrival = arrivals[0]
    # we need time since start of the record
    minloc = arrival.time + (etime - stream[0].stats.starttime)
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
    min_noise_dur = CONFIG["windows"]["window_checks"]["min_noise_duration"]
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
        fmt = "Noise window (%.1f s) less than minimum (%.1f)"
        tpl = (minloc, min_noise_dur)
        raise ValueError(fmt % tpl)
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
        picker_config = CONFIG["pickers"]
    min_noise_dur = CONFIG["windows"]["window_checks"]["min_noise_duration"]
    params = picker_config["power"]
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
        fmt = "Noise window (%.1f s) less than minimum (%.1f)"
        tpl = (minloc, min_noise_dur)
        raise ValueError(fmt % tpl)
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
    apn = np.mean(np.power(noise, 2))  # average power of noise
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
        raise (ve)

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
        signal = np.array(trace.data, dtype=float)
        noise = np.array(trace.data, dtype=float)[0 : int(minloc / dt)]
        aps = np.mean(np.power(signal, 2))  # average power of signal
        if aps == 0:
            trace.fail("Signal window mean is 0.")
            snr_values.append(0.0)
            continue
        if len(noise) != 0:
            apn = np.mean(np.power(noise, 2))  # average power of noise
        else:
            apn = 0.0

        # Keep this separate from above if-else because apn could be zero
        # even if len > 0.
        if apn == 0:
            apn = 0.00001
            logging.warning(f"Noise window for {trace.get_id()} has mean of zero.")
        # signal-to-noise ratio in decibel
        snr_i = 10 * np.math.log10(aps / apn)
        snr_values.append(snr_i)

    return np.mean(snr_values)


def pphase_pick(trace, period=None, damping=0.6, nbins=None, peak_selection=False):
    """Compute P-phase arrival time.

    Adapted from Python code written by Francisco Hernandez of the Puerto Rico
    Strong Motion Program. That code was in turn adapted from Matlab code written by
    Dr. Erol Kalkan, P.E. The algorithms are described here in full:

    Kalkan, E. (2016). "An automatic P-phase arrival time picker", Bull. of
    Seismol. Soc. of Am., 106, No. 3, doi: 10.1785/0120150111

    Args:
        trace (StationTrace):
            StationTrace containing waveform (acceleration or velocity) data.
        period (float):
            Undamped natural period of the sensor in seconds. Defaults to 0.01s for
            sample rates >= 100, 0.1s for sample rates < 100.
        damping (float):
            Damping ratio.
        nbins (int):
            Histogram bin size (default is 2/sampling interval). Regional or
            teleseismic records may need different values of bin size for better
            picking results)
        selection (Selector):
            One of:
                Selector.TO_PEAK - take segment of waveform from beginning to absolute
                    peak value (recommended for fast processing).
                Selector.FULL - take full waveform.

    Returns:
        tuple:
            - Float number of seconds from start of trace to P-Phase beginning.
            - Signal-to-noise ratio in decibels
    """
    WAVEFORM_TYPES = {"acc": "sm", "vel": "wm"}
    wftype = WAVEFORM_TYPES[trace.stats.standard["units_type"]]
    if period == "None":
        if trace.stats.sampling_rate >= 100:
            period = 0.01
        else:
            period = 0.1

    if nbins == "None":
        nbins = 2 / trace.stats.delta

    if wftype == "wm":
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

    if filtflag != 0:
        trace_copy.filter(
            type="bandpass", freqmin=flp, freqmax=fhp, corners=4, zerophase=True
        )
        trace_copy.detrend(type="linear")

    if peak_selection == "True":
        ind_peak = np.nonzero(
            np.abs(trace_copy.data) == np.max(np.abs(trace_copy.data))
        )
        trace_copy.data = trace_copy.data[0 : ind_peak[0][0]]

    # Construct a fixed-base viscously damped SDF oscillator
    omegan = 2 * np.pi / period  # natural frequency in radian/second
    C = 2 * damping * omegan  # viscous damping term
    K = omegan**2  # stiffness term
    y = np.zeros((2, len(trace_copy.data)))  # response vector

    # Solve second-order ordinary differential equation of motion
    A = np.array([[0, 1], [-K, -C]])
    Ae = alg.expm(A * dt)
    AeB = np.dot(alg.lstsq(A, (Ae - np.identity(2)))[0], np.array((0, 1)))

    for k in range(1, len(trace_copy.data)):
        y[:, k] = np.dot(Ae, y[:, k - 1]) + AeB * trace_copy.data[k]

    # relative velocity of mass
    veloc = y[1, :]
    # integrand of viscous damping energy
    Edi = np.dot(2 * damping * omegan, np.power(veloc, 2))

    # Apply histogram method
    levels, histogram, bins = _get_statelevel(Edi, nbins)
    locs = np.nonzero(Edi > levels[0])[0]
    # get zero crossings
    indx = np.nonzero(
        np.multiply(trace_copy.data[0 : locs[0] - 1], trace_copy.data[1 : locs[0]]) < 0
    )[0]
    TF = indx.size

    # Update first onset
    if TF != 0:
        loc = (indx[TF - 1] + 1) * dt
    else:
        # try nbins/2
        levels, histogram, bins = _get_statelevel(Edi, np.ceil(nbins / 2))
        locs = np.nonzero(Edi > levels[0])[0]
        # get zero crossings
        indx = np.nonzero(
            np.multiply(trace_copy.data[0 : locs[0] - 1], trace_copy.data[1 : locs[0]])
            < 0
        )[0]
        TF = indx.size
        if TF != 0:
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
    lHist = histogram[int(lLow) : int(lHigh)]
    uHist = histogram[int(uLow) : int(uHigh)]

    levels = np.zeros(2)
    iMax = np.argmax(lHist[1, :])
    iMin = np.argmax(uHist)
    levels[0] = ymin + dy * (lLow + iMax + 0.5)
    levels[1] = ymin + dy * (uLow + iMin + 0.5)

    # Lowest histogram bin numbers for upper and lower histograms
    # lHist_final = (lLow + iMax);
    # uHist_final = (uLow + iMin);
    return levels, histogram, bins


def create_travel_time_dataframe(streams, catalog_file, ddepth, ddist, model):
    """
    Creates a travel time dataframe, which contains the phase arrrival times
    for each station the StreamCollection, for each event in the catalog.
    This uses an interpolation method to save time, and the fineness of the
    interpolation grid can be adjusted using the ddepth and ddist parameters.
    Using the recommended values of ddepth=5 and ddist=0.1 are generally
    sufficient to achieve less than 0.1 seconds of error in the travel times,
    for most cases.

    Args:
        streams (StreamCollection):
            Streams to calculate travel times for.
        catalog_file (str):
            The path to the CSV file (from ComCat) which contains event info.
        ddepth (float):
            The depth spacing (in km) for the interpolation grid.
            Recommended value is 5 km.
        ddist (float):
            The distance spacing (in decimal degrees) for the interpolation
            grid. Recommend value is 0.1 degrees.

    Retuns:
        A tuple, containing the travel time dataframe and the catalog
        (list of ScalarEvent objects).
    """

    # Read the catalog file and create a catalog (list) of ScalarEvent objects
    df_catalog = pd.read_csv(catalog_file)

    # Replace any negative depths with 0
    df_catalog["depth"].clip(lower=0, inplace=True)
    catalog = []
    for idx, row in df_catalog.iterrows():
        event = ScalarEvent()
        event.fromParams(
            row["id"],
            row["time"],
            row["latitude"],
            row["longitude"],
            row["depth"],
            row["mag"],
        )
        catalog.append(event)

    # Store the lat, lon, and id for each stream
    st_lats, st_lons, st_ids = [], [], []
    for st in streams:
        st_lats.append(st[0].stats.coordinates.latitude)
        st_lons.append(st[0].stats.coordinates.longitude)
        st_ids.append(st[0].stats.network + "." + st[0].stats.station)

    # Calculate the distance for each stream, for each event
    # Store distances in a matrix
    distances_matrix = np.zeros((len(streams), len(catalog)))
    for idx, st in enumerate(streams):
        distances_matrix[idx] = locations2degrees(
            np.repeat(st_lats[idx], len(catalog)),
            np.repeat(st_lons[idx], len(catalog)),
            df_catalog["latitude"],
            df_catalog["longitude"],
        )
    distances_matrix = distances_matrix.T

    # Calculate the minimum depth/distance values for the inteprolation grid
    # This includes a buffer to avoid interpolating at the endpoints
    # Make sure that the minimum depth/distance values aren't negative
    minimum_depth = max([0, min(df_catalog["depth"]) - 2 * ddepth])
    minimum_dist = max([0, distances_matrix.min() - 2 * ddist])
    depth_grid = np.arange(minimum_depth, max(df_catalog["depth"]) + 2 * ddepth, ddepth)
    distance_grid = np.arange(minimum_dist, distances_matrix.max() + 2 * ddist, ddist)

    # For each distance and each depth, compute the travel time
    # Store values in the "times" 2D matrix
    taupy_model = TauPyModel(model)
    times = np.zeros((len(depth_grid), len(distance_grid)))
    for i, depth in enumerate(depth_grid):
        for j, dist in enumerate(distance_grid):
            arrivals = taupy_model.get_travel_times(depth, dist, ["p", "P", "Pn"])
            if not arrivals:
                times[i][j] = np.nan
            else:
                times[i][j] = arrivals[0].time

    # Use 2D interpolation to interpolate values at the actual points
    points = np.transpose(
        [
            np.tile(distance_grid, len(depth_grid)),
            np.repeat(depth_grid, len(distance_grid)),
        ]
    )
    new_points = np.vstack(
        (distances_matrix.flatten(), np.repeat(df_catalog["depth"], len(streams)))
    ).T
    interpolated_times = griddata(points, times.flatten(), new_points).reshape(
        (-1, len(streams))
    )
    utcdatetimes = np.array([UTCDateTime(time) for time in df_catalog["time"]])
    interpolated_times = utcdatetimes.reshape(-1, 1) + interpolated_times

    # Store travel time information in a DataFrame
    # Column indicies are the station ids, rows are the earthquake ids
    df = pd.DataFrame(data=interpolated_times, index=df_catalog["id"], columns=st_ids)

    # Remove any duplicate columns which might result from a station with
    # multiple instruments
    df = df.loc[:, ~df.columns.duplicated()]
    return df, catalog
