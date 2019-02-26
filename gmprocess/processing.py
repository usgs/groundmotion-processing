#!/usr/bin/env python
"""
Processing methods.
"""

import sys
import numpy as np
import logging

from scipy.optimize import curve_fit

from gmprocess.config import get_config
import gmprocess.pretesting as pretesting
from gmprocess.windows import signal_split
from gmprocess.windows import signal_end
from gmprocess.utils import _update_provenance, _get_provenance
from gmprocess import corner_frequencies

CONFIG = get_config()

TAPER_TYPES = {'cosine': 'Cosine',
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
               'triang': 'Triangular'}


def process_streams(streams, origin, config=None):
    """Run processing steps from the config file.

    This method removes streams based on the 'pretesting' config section, and
    sets the noise and signal windows based on the 'windows' config section.

    Then it looks in the 'processing' config section and loops  over those
    steps and hands off the config options to the appropriate prcessing method.

    Args:
        streams (list):
            List of obspy streams where each stream is a group of channels from
            the same station.
        origin (dict):
            Dictionary with the following keys:
              - eventid
              - magnitude
              - time (UTCDateTime object)
              - lon
              - lat
              - depth
        config (dict): Configuration dictionary (or None). See get_config().

    Returns:
        list: List of processed obspy streams.
    """
    if config is None:
        config = CONFIG

    logging.info('Processing streams...')

    # -------------------------------------------------------------------------
    # Begin pre-testing steps
    logging.info('Starting pre-testing...')
    stalta_args = config['pretesting']['stalta']
    amplitude_args = config['pretesting']['amplitude']

    streams_passed = []

    for stream in streams:
        # Make a copy because python sucks
        sp = stream.copy()

        # STA/LTA check
        logging.debug('len(stream): %s (before stalta)' % len(stream))
        sp = pretesting.check_sta_lta(sp, **stalta_args)
        logging.debug('len(sp): %s (after stalta)' % len(sp))

        # Aplitude check
        sp = pretesting.check_max_amplitude(sp, **amplitude_args)
        logging.debug('len(sp): %s (after amp check)' % len(sp))
        if len(sp) > 0:
            streams_passed.append(sp)

    if len(streams_passed) == 0:
        logging.info('No streams passed pre-testing checks. Exiting.')
        sys.exit(1)

    # -------------------------------------------------------------------------
    # Begin noise/signal window steps
    logging.info('Windowing noise and signal...')
    window_conf = config['windows']

    for stream in streams_passed:
        # Estimate noise/signal split time
        split_conf = window_conf['split']
        event_time = origin['time']
        event_lon = origin['lon']
        event_lat = origin['lat']
        stream = signal_split(
            stream,
            event_time=event_time,
            event_lon=event_lon,
            event_lat=event_lat,
            **split_conf)

        # Estimate end of signal
        end_conf = window_conf['signal_end']
        event_mag = origin['magnitude']
        stream = signal_end(
            stream,
            event_time=event_time,
            event_lon=event_lon,
            event_lat=event_lat,
            event_mag=event_mag,
            **end_conf
        )

    # -------------------------------------------------------------------------
    # Begin corner frequency stuff
    logging.info('Setting corner frequencies...')
    cf_config = config['corner_frequencies']

    for stream in streams_passed:
        if cf_config['method'] == 'constant':
            stream = corner_frequencies.constant(stream)
        elif cf_config['method'] == 'snr':
            snr_config = cf_config['snr']
            stream = corner_frequencies.snr(stream, **snr_config)

    # -------------------------------------------------------------------------
    # Begin processing steps
    logging.info('Starting processing...')
    processing_steps = config['processing']

    # Loop over streams
    processed_streams = []
    for stream in streams_passed:
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
            stream = globals()[step_name](
                stream,
                **step_args
            )
        processed_streams.append(stream)
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
        st (obspy.core.stream.Stream):
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
        obspy.core.stream.Stream: Instrument-response-corrected stream.
    """

    if output not in ['ACC', 'VEL', 'DISP']:
        raise ValueError('Output value of %s is invalid. Must be ACC, VEL, '
                         'or DISP.' % output)

    # Check if the response information is already attached in the trace stats
    for tr in st:
        f_n = 0.5 / tr.stats.delta
        if f3 is None:
            f3 = 0.9 * f_n
        if f4 is None:
            f4 = f_n
        # Check if we have an instrument measuring velocity or accleration
        if tr.stats.channel[1] == 'H':
            tr.remove_response(
                inventory=inv, output=output, water_level=water_level,
                pre_filt=(f1, f2, f3, f4))
            tr = _update_provenance(
                tr, 'remove_response',
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
            tr = _update_provenance(
                tr, 'remove_response',
                {
                    'method': 'remove_sensitivity',
                    'inventory': inv
                }
            )
        else:
            raise ValueError(
                'This instrument type is not supported. '
                'The instrument code must be either H '
                '(high gain seismometer) or N (accelerometer).')
    return st


def detrend(st, detrending_method=None):
    """Detrend stream.

    Args:
        st (obspy.core.stream.Stream):
            Stream of data.
        method (str): Method to detrend; valid options include the 'type'
            options supported by obspy.core.trace.Trace.detrend as well as
            'baseline_sixth_order', which is for a baseline correction method
            that fits a sixth-order polynomial to the displacement time series,
            and sets the zeroth- and first-order terms to be zero. The second
            derivative of the fit polynomial is then removed from the
            acceleration time series.

    Returns:
        obspy.core.stream.Stream: Detrended stream.
    """

    for tr in st:
        if detrending_method == 'baseline_sixth_order':
            tr = _correct_baseline(tr)
        else:
            tr = tr.detrend(detrending_method)

        tr = _update_provenance(
            tr, 'detrend',
            {
                'detrending_method': detrending_method
            }
        )

    return st


def cut(st, sec_before_split=None):
    """ Cut/trim the record.

    This method minimally requires that the windows.signal_end method has been
    run, in which case the record is trimmed to the end of the signal that
    was estimated by that method.

    To trim the beginning of the record, the sec_before_split must be
    specified, which uses the noise/signal split time that was estiamted by the
    windows.signal_split mehtod.

    Args:
        st (obspy.core.stream.Stream):
            Stream of data.
        sec_before_split (float):
            Seconds to trim before split. If None, then the beginning of the
            record will be unchanged.

    Returns:
        stream: cut streams.
    """
    for tr in st:
        logging.debug('Before cut end time: %s ' % tr.stats.endtime)
        etime = _get_provenance(tr, 'signal_end')[0]['end_time']
        tr.trim(endtime=etime)
        logging.debug('After cut end time: %s ' % tr.stats.endtime)
        if sec_before_split is not None:
            split_time = _get_provenance(tr, 'signal_split')[0]['split_time']
            stime = split_time - sec_before_split
            logging.debug('Before cut start time: %s ' % tr.stats.starttime)
            tr.trim(starttime=stime)
            logging.debug('After cut start time: %s ' % tr.stats.starttime)
        tr = _update_provenance(
            tr, 'cut',
            {
                'new_start_time': tr.stats.starttime,
                'new_end_time': tr.stats.endtime
            }
        )
    return st


def highpass_filter(st, filter_order=5, number_of_passes=2):
    """Highpass filter.

    Args:
        st (obspy.core.stream.Stream):
            Stream of data.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.

    Returns:
        stream: Filtered streams.
    """
    if number_of_passes == 1:
        zerophase = False
    elif number_of_passes == 2:
        zerophase = True
    else:
        raise ValueError("number_of_passes must be 1 or 2.")

    for tr in st:
        freq = 0.08
        tr.filter(type="highpass",
                  freq=freq,
                  corners=filter_order,
                  zerophase=zerophase)
        tr = _update_provenance(
            tr, 'highpass_filter',
            {
                'filter_type': 'Butterworth',
                'filter_order': filter_order,
                'number_of_passes': number_of_passes,
                'corner_frequency': freq
            }
        )
    return st


def lowpass_filter(st, filter_order=5, number_of_passes=2):
    """Lowpass filter.

    Args:
        st (obspy.core.stream.Stream):
            Stream of data.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.

    Returns:
        stream: Filtered streams.
    """
    if number_of_passes == 1:
        zerophase = False
    elif number_of_passes == 2:
        zerophase = True
    else:
        raise ValueError("number_of_passes must be 1 or 2.")

    for tr in st:
        freq = 20.0
        tr.filter(type="lowpass",
                  freq=freq,
                  corners=filter_order,
                  zerophase=zerophase)
        tr = _update_provenance(
            tr, 'lowpass_filter',
            {
                'filter_type': 'Butterworth',
                'filter_order': filter_order,
                'number_of_passes': number_of_passes,
                'corner_frequency': freq
            }
        )
    return st


def taper(st, type="hann", width=0.05, side="both"):
    """Taper streams.

    Args:
        st (obspy.core.stream.Stream):
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
    for tr in st:
        tr.taper(max_percentage=width, type=type, side=side)
        window_type = TAPER_TYPES[type]
        tr = _update_provenance(tr, 'taper',
                                {'window_type': window_type,
                                 'taper_width': width,
                                 'side': side})
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
    orig_trace = trace.copy()
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
    for i in range(orig_trace.stats.npts):
        orig_trace.data[i] -= polynomial_second_derivative(i)
    orig_trace = _update_provenance(
        orig_trace, 'baseline',
        {
            'polynomial_coefs': poly_cofs
        }
    )

    return orig_trace


def _poly_func(x, a, b, c, d, e):
    """
    Model polynomial function for polynomial baseline correction.
    """
    return a * x**6 + b * x**5 + c * x**4 + d * x**3 + e * x**2
