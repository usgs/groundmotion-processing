#!/usr/bin/env python
"""
Processing methods.
"""

import numpy as np
import logging

from scipy.optimize import curve_fit

from gmprocess.streamcollection import StreamCollection
from gmprocess.config import get_config
from gmprocess.windows import signal_split
from gmprocess.windows import signal_end
from gmprocess.windows import window_checks
from gmprocess import corner_frequencies
from gmprocess.snr import compute_snr

# -----------------------------------------------------------------------------
# Note: no QA on following imports because they need to be in namespace to be
# discovered. They are not called directly so linters will think this is a
# mistake.
from gmprocess.pretesting import (  # NOQA
    check_max_amplitude,
    check_sta_lta,
    check_free_field)
from gmprocess.spectrum import fit_spectra  # NOQA
from gmprocess.plot import summary_plots  # NOQA
from gmprocess.report import build_report  # NOQA
# -----------------------------------------------------------------------------

M_TO_CM = 100.0

# List of processing steps that require an origin
# besides the arguments in the conf file.
REQ_ORIGIN = [
    'build_report',
    'summary_plots'
]


TAPER_TYPES = {
    'cosine': 'Cosine',
    'barthann': 'Bartlett-Hann',
    'bartlett': 'Bartlett',
    'blackman': 'Blackman',
    'blackmanharris': 'Blackman-Harris',
    'bohman': 'Bohman',
    'boxcar': 'Boxcar',
    'chebwin': 'Dolph-Chebyshev',
    'flattop': 'Flat top',
    'gaussian': 'Gaussian',
    'general_gaussian': 'Generalized Gaussian',
    'hamming': 'Hamming',
    'hann': 'Hann',
    'kaiser': 'Kaiser',
    'nuttall': 'Blackman-Harris according to Nuttall',
    'parzen': 'Parzen',
    'slepian': 'Slepian',
    'triang': 'Triangular'
}


def process_streams(streams, origin, config=None):
    """
    Run processing steps from the config file.

    This method looks in the 'processing' config section and loops over those
    steps and hands off the config options to the appropriate prcessing method.
    Streams that fail any of the tests are kepth in the StreamCollection but
    the parameter 'passed_checks' is set to False and subsequent processing
    steps are not applied once a check has failed.

    Args:
        streams (list):
            A StreamCollection object.
        origin (dict):
            Dictionary with the following keys:
              - id
              - magnitude
              - time (UTCDateTime object)
              - lon
              - lat
              - depth
        config (dict): Configuration dictionary (or None). See get_config().

    Returns:
        A StreamCollection object.
    """

    if not isinstance(streams, StreamCollection):
        raise ValueError('streams must be a StreamCollection instance.')

    if config is None:
        config = get_config()

    logging.info('Processing streams...')

    event_time = origin['time']
    event_lon = origin['lon']
    event_lat = origin['lat']

    # -------------------------------------------------------------------------
    # Begin noise/signal window steps

    logging.info('Windowing noise and signal...')
    window_conf = config['windows']

    processed_streams = streams.copy()
    for st in processed_streams:
        logging.info('Checking stream %s...' % st.get_id())
        # Estimate noise/signal split time
        split_conf = window_conf['split']
        st = signal_split(
            st,
            event_time=event_time,
            event_lon=event_lon,
            event_lat=event_lat,
            **split_conf)

        # Estimate end of signal
        end_conf = window_conf['signal_end']
        event_mag = origin['magnitude']
        st = signal_end(
            st,
            event_time=event_time,
            event_lon=event_lon,
            event_lat=event_lat,
            event_mag=event_mag,
            **end_conf
        )
        wcheck_conf = window_conf['window_checks']
        if wcheck_conf['do_check']:
            st = window_checks(
                st,
                min_noise_duration=wcheck_conf['min_noise_duration'],
                min_signal_duration=wcheck_conf['min_signal_duration']
            )

    # -------------------------------------------------------------------------
    # Begin processing steps
    logging.info('Starting processing...')
    processing_steps = config['processing']

    # Loop over streams
    for stream in processed_streams:
        logging.info('Stream: %s' % stream.get_id())
        for processing_step_dict in processing_steps:

            key_list = list(processing_step_dict.keys())
            if len(key_list) != 1:
                raise ValueError(
                    'Each processing step must contain exactly one key.')
            step_name = key_list[0]

            logging.info('Processing step: %s' % step_name)
            step_args = processing_step_dict[step_name]
            # Using globals doesn't seem like a great solution here, but it
            # works.
            if step_name not in globals():
                raise ValueError(
                    'Processing step %s is not valid.' % step_name)

            # Origin is required by some steps and has to be handled specially.
            # There must be a better solution for this...
            if step_name == 'fit_spectra':
                step_args = {
                    'origin': origin
                }
            elif step_name in REQ_ORIGIN:
                step_args['origin'] = origin

            if step_args is None:
                stream = globals()[step_name](stream)
            else:
                stream = globals()[step_name](stream, **step_args)

    # Build the summary report?
    build_conf = config['build_report']
    if build_conf['run']:
        build_report(processed_streams,
                     build_conf['directory'],
                     origin, config=config)

    logging.info('Finished processing streams.')
    return processed_streams


def remove_response(st, f1, f2, f3=None, f4=None, water_level=None,
                    output='ACC', inv=None):
    """
    Performs instrument response correction. If the response information is
    not already attached to the stream, then an inventory object must be
    provided. If the instrument is a strong-motion accelerometer, then
    tr.remove_sensitivity() will be used. High-gain seismometers will use
    tr.remove_response() with the defined pre-filter and water level.

    If f3 is Null it will be set to 0.9*fn, if f4 is Null it will be set to fn.

    Args:
        st (StationStream):
            Stream of data.
        f1 (float):
            Frequency 1 for pre-filter.
        f2 (float):
            Frequency 2 for pre-filter.
        f3 (float):
            Frequency 3 for pre-filter.
        f4 (float):
            Frequency 4 for pre-filter.
        water_level (float):
            Water level for deconvolution.
        output (str):
            Outuput units. Must be 'ACC', 'VEL', or 'DISP'.
        inv (obspy.core.inventory.inventory):
            Obspy inventory object containing response information.

    Returns:
        StationStream: Instrument-response-corrected stream.
    """

    if output not in ['ACC', 'VEL', 'DISP']:
        raise ValueError('Output value of %s is invalid. Must be ACC, VEL, '
                         'or DISP.' % output)

    # Check if the response information is already attached in the trace stats
    for tr in st:

        # Check if this trace has already been converted to physical units
        if 'remove_response' in tr.getProvenanceKeys():
            logging.info('Trace has already had instrument response removed. '
                         'Nothing to be done.')
            continue

        f_n = 0.5 / tr.stats.delta
        if f3 is None:
            f3 = 0.9 * f_n
        if f4 is None:
            f4 = f_n
        # Check if we have an instrument measuring velocity or accleration
        if tr.stats.channel[1] == 'H':
            # Attempting to remove instrument response can cause a variety
            # errors due to bad response metadata
            try:
                tr.remove_response(
                    inventory=inv, output=output, water_level=water_level,
                    pre_filt=(f1, f2, f3, f4))
            except Exception as e:
                reason = ('Encountered an error when attempting to remove '
                          'instrument response: ' + e)
                tr.fail(reason)
                continue

            # Response removal can also result in NaN values due to bad
            # metadata, so check that data contains no NaN or inf values
            if not np.isfinite(tr.data).all():
                reason = ('Non-finite values encountered after removing '
                          'instrument response.')
                tr.fail(reason)
                continue

            tr.data *= M_TO_CM  # Convert from m/s/s to cm/s/s
            tr.setProvenance(
                'remove_response',
                {
                    'method': 'remove_sensitivity',
                    'inventory': inv,
                    'f1': f1,
                    'f2': f2,
                    'f3': f3,
                    'f4': f4,
                    'water_level': water_level
                }
            )
        elif tr.stats.channel[1] == 'N':
            tr.remove_sensitivity(inventory=inv)
            tr.data *= M_TO_CM  # Convert from m/s/s to cm/s/s
            tr.setProvenance(
                'remove_response',
                {
                    'method': 'remove_sensitivity',
                    'inventory': inv
                }
            )
        else:
            reason = ('This instrument type is not supported. '
                      'The instrument code must be either H '
                      '(high gain seismometer) or N (accelerometer).')
            tr.fail(reason)

    return st


def detrend(st, detrending_method=None):
    """
    Detrend stream.

    Args:
        st (StationStream):
            Stream of data.
        method (str): Method to detrend; valid options include the 'type'
            options supported by obspy.core.trace.Trace.detrend as well as
            'baseline_sixth_order', which is for a baseline correction method
            that fits a sixth-order polynomial to the displacement time series,
            and sets the zeroth- and first-order terms to be zero. The second
            derivative of the fit polynomial is then removed from the
            acceleration time series.

    Returns:
        StationStream: Detrended stream.
    """

    for tr in st:
        if detrending_method == 'baseline_sixth_order':
            tr = _correct_baseline(tr)
        else:
            tr = tr.detrend(detrending_method)

        tr.setProvenance(
            'detrend',
            {
                'detrending_method': detrending_method
            }
        )

    return st


def resample(st, new_sampling_rate=None, method=None, a=None):
    """
    Resample stream.

    Args:
        st (StationStream):
            Stream of data.
        sampling_rate (float):
            New sampling rate, in Hz.
        method (str):
            Method for interpolation. Currently only supports 'lanczos'.
        a (int):
            Width of the Lanczos window, in number of samples.

    Returns:
        StationStream: Resampled stream.
    """
    if not st.passed:
        return st

    if method != 'lanczos':
        raise ValueError('Only lanczos interpolation method is supported.')

    for tr in st:
        tr.interpolate(sampling_rate=new_sampling_rate, method=method, a=a)
        tr.setProvenance(
            'resample',
            {
                'new_sampling_rate': new_sampling_rate
            }
        )

    return st


def cut(st, sec_before_split=None):
    """
    Cut/trim the record.

    This method minimally requires that the windows.signal_end method has been
    run, in which case the record is trimmed to the end of the signal that
    was estimated by that method.

    To trim the beginning of the record, the sec_before_split must be
    specified, which uses the noise/signal split time that was estiamted by the
    windows.signal_split mehtod.

    Args:
        st (StationStream):
            Stream of data.
        sec_before_split (float):
            Seconds to trim before split. If None, then the beginning of the
            record will be unchanged.

    Returns:
        stream: cut streams.
    """
    if not st.passed:
        return st

    for tr in st:
        logging.debug('Before cut end time: %s ' % tr.stats.endtime)
        etime = tr.getParameter('signal_end')['end_time']
        tr.trim(endtime=etime)
        logging.debug('After cut end time: %s ' % tr.stats.endtime)
        if sec_before_split is not None:
            split_time = tr.getParameter('signal_split')['split_time']
            stime = split_time - sec_before_split
            logging.debug('Before cut start time: %s ' % tr.stats.starttime)
            if stime < etime:
                tr.trim(starttime=stime)
            else:
                tr.fail('The \'cut\' processing step resulting in '
                        'incompatible start and end times.')
            logging.debug('After cut start time: %s ' % tr.stats.starttime)
        tr.setProvenance(
            'cut',
            {
                'new_start_time': tr.stats.starttime,
                'new_end_time': tr.stats.endtime
            }
        )
    return st


def get_corner_frequencies(st, method='constant', constant=None, snr=None):
    """
    Select corner frequencies.

    Args:
        st (StationStream):
            Stream of data.
        method (str):
            Which method to use; currently allowed "snr" or "constant".
        constant(dict):
            Dictionary of `constant` method config options.
        snr (dict):
            Dictionary of `snr` method config options.

    Returns:
        strea: Stream with selected corner frequencies added.
    """

    logging.info('Setting corner frequencies...')
    if method == 'constant':
        st = corner_frequencies.constant(st, **constant)
    elif method == 'snr':
        st = corner_frequencies.snr(st, **snr)
    else:
        raise ValueError("Corner frequency 'method' must be either "
                         "'constant' or 'snr'.")
    return st


def highpass_filter(st, filter_order=5, number_of_passes=2):
    """
    Highpass filter.

    Args:
        st (StationStream):
            Stream of data.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.

    Returns:
        stream: Filtered streams.
    """
    if not st.passed:
        return st

    if number_of_passes == 1:
        zerophase = False
    elif number_of_passes == 2:
        zerophase = True
    else:
        raise ValueError("number_of_passes must be 1 or 2.")

    for tr in st:
        freq_prov = tr.getParameter('corner_frequencies')
        freq = freq_prov['highpass']
        tr.filter(type="highpass",
                  freq=freq,
                  corners=filter_order,
                  zerophase=zerophase)
        tr.setProvenance(
            'highpass_filter',
            {
                'filter_type': 'Butterworth',
                'filter_order': filter_order,
                'number_of_passes': number_of_passes,
                'corner_frequency': freq
            }
        )
    return st


def lowpass_filter(st, filter_order=5, number_of_passes=2):
    """
    Lowpass filter.

    Args:
        st (StationStream):
            Stream of data.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.

    Returns:
        stream: Filtered streams.
    """
    if not st.passed:
        return st

    if number_of_passes == 1:
        zerophase = False
    elif number_of_passes == 2:
        zerophase = True
    else:
        raise ValueError("number_of_passes must be 1 or 2.")

    for tr in st:
        freq_prov = tr.getParameter('corner_frequencies')
        freq = freq_prov['lowpass']

        # Only perform low pass filter if corner is less than Nyquist frequency
        # (half of the sampling rate)
        if freq >= (0.5 * tr.stats.sampling_rate):
            continue

        tr.filter(type="lowpass",
                  freq=freq,
                  corners=filter_order,
                  zerophase=zerophase)
        tr.setProvenance(
            'lowpass_filter',
            {
                'filter_type': 'Butterworth',
                'filter_order': filter_order,
                'number_of_passes': number_of_passes,
                'corner_frequency': freq
            }
        )
    return st


def taper(st, type="hann", width=0.05, side="both"):
    """
    Taper streams.

    Args:
        st (StationStream):
            Stream of data.
        type (str):
            Taper type.
        width (float):
            Taper width as percentage of trace length.
        side (str):
            Valid options: "both", "left", "right".

    Returns:
        stream: tapered streams.
    """
    if not st.passed:
        return st

    for tr in st:
        tr.taper(max_percentage=width, type=type, side=side)
        window_type = TAPER_TYPES[type]
        tr.setProvenance(
            'taper',
            {
                'window_type': window_type,
                'taper_width': width,
                'side': side}
        )
    return st


def snr_check(st, threshold=3.0, min_freq=0.2, max_freq=5.0, bandwidth=20.0):
    """
    Check signal-to-noise ratio.

    Requires noise/singal windowing to have succeeded.

    Args:
        st (StationStream):
            Stream of data.
        threshold (float):
            Threshold SNR value.
        min_freq (float):
            Minimum frequency for threshold to be exeeded.
        max_freq (float):
            Maximum frequency for threshold to be exeeded.
        bandwidth (float):
            Konno-Omachi smoothing bandwidth parameter.

    Returns:
        stream: Streams with SNR calculations and checked that they pass the
        configured criteria.
    """

    for tr in st:
        # Comput SNR
        tr = compute_snr(tr, bandwidth)

        if st.passed and tr.hasParameter('snr'):
            snr_dict = tr.getParameter('snr')
            snr = np.array(snr_dict['snr'])
            freq = np.array(snr_dict['freq'])
            # Check if signal criteria is met
            min_snr = np.min(snr[(freq >= min_freq) & (freq <= max_freq)])
            if min_snr < threshold:
                tr.fail('Failed SNR check; SNR less than threshold.')
        snr_conf = {
            'threshold': threshold,
            'min_freq': min_freq,
            'max_freq': max_freq,
            'bandwidth': bandwidth
        }
        tr.setParameter('snr_conf', snr_conf)
    return st


def max_traces(st, n_max=3):
    """
    Reject a stream if it has more than n_max traces.

    The purpose of this is to skip over stations with muliple strong motion
    instruments, which can occur with downhole or structural arrays since our
    code currently is not able to reliably group by location within an array.

    Args:
        st (StationStream):
            Stream of data.
        n_max (int):
            Maximum allowed number of streams; default to 3.

    Returns:
        Stream with adjusted failed fields.
    """
    if not st.passed:
        return st

    logging.debug('Starting max_traces')
    logging.debug('len(st) = %s' % len(st))
    if len(st) > n_max:
        for tr in st:
            tr.fail('More than %s traces in stream.' % n_max)
    return st


def _correct_baseline(trace):
    """
    Performs a baseline correction following the method of Ancheta
    et al. (2013). This removes low-frequency, non-physical trends
    that remain in the time series following filtering.

    Args:
        trace (obspy.core.trace.Trace):
            Trace of strong motion data.

    Returns:
        trace: Baseline-corrected trace.
    """

    # Make copies of the trace for our accleration data
    acc_trace = trace.copy()

    # Integrate twice to get the displacement time series
    disp_trace = (acc_trace.integrate()).integrate()

    # Fit a sixth order polynomial to displacement time series, requiring
    # that the 1st and 0th order coefficients are zero
    time_values = np.linspace(0, trace.stats.npts - 1, trace.stats.npts)
    poly_cofs = list(curve_fit(_poly_func, time_values, disp_trace.data)[0])
    poly_cofs += [0, 0]

    # Construct a polynomial from the coefficients and compute
    # the second derivative
    polynomial = np.poly1d(poly_cofs)
    polynomial_second_derivative = np.polyder(polynomial, 2)

    # Subtract the second derivative of the polynomial from the
    # acceleration trace
    for i in range(trace.stats.npts):
        trace.data[i] -= polynomial_second_derivative(i)
    trace.setParameter('baseline', {'polynomial_coefs': poly_cofs})

    return trace


def _poly_func(x, a, b, c, d, e):
    """
    Model polynomial function for polynomial baseline correction.
    """
    return a * x**6 + b * x**5 + c * x**4 + d * x**3 + e * x**2
