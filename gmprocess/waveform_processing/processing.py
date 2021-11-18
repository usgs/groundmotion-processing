#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Processing methods.
"""

import numpy as np
import logging

from obspy.taup import TauPyModel
from scipy.optimize import curve_fit
from scipy.integrate import cumtrapz

from gmprocess.core.stationtrace import PROCESS_LEVELS
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.config import get_config
from gmprocess.waveform_processing.windows import \
    signal_split, signal_end, window_checks
from gmprocess.waveform_processing.phase import create_travel_time_dataframe
from gmprocess.waveform_processing import corner_frequencies

# -----------------------------------------------------------------------------
# Note: no QA on following imports because they need to be in namespace to be
# discovered. They are not called directly so linters will think this is a
# mistake.
from gmprocess.waveform_processing.pretesting import (  # NOQA
    check_max_amplitude,
    check_sta_lta,
    check_free_field)
from gmprocess.waveform_processing.filtering import \
    lowpass_filter, highpass_filter  # NOQA
from gmprocess.waveform_processing.adjust_highpass import \
    adjust_highpass_corner  # NOQA
from gmprocess.waveform_processing.zero_crossings import \
    check_zero_crossings  # NOQA
from gmprocess.waveform_processing.nn_quality_assurance import \
    NNet_QA  # NOQA
from gmprocess.waveform_processing.snr import compute_snr  # NOQA
from gmprocess.waveform_processing.spectrum import fit_spectra  # NOQA
from gmprocess.waveform_processing.windows import \
    cut, trim_multiple_events  # NOQA
from gmprocess.waveform_processing.clipping.clipping_check import \
    check_clipping  # NOQA
from gmprocess.waveform_processing.sanity_checks import check_tail  # NOQA
# -----------------------------------------------------------------------------

M_TO_CM = 100.0

# List of processing steps that require an origin
# besides the arguments in the conf file.
REQ_ORIGIN = ['fit_spectra', 'trim_multiple_events', 'check_clipping']


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

ABBREV_UNITS = {'ACC': 'cm/s^2',
                'VEL': 'cm/s',
                'DISP': 'cm'}


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
        origin (ScalarEvent):
            ScalarEvent object.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        A StreamCollection object.
    """

    if not isinstance(streams, StreamCollection):
        raise ValueError('streams must be a StreamCollection instance.')

    if config is None:
        config = get_config()

    event_time = origin.time
    event_lon = origin.longitude
    event_lat = origin.latitude

    # -------------------------------------------------------------------------
    # Compute a travel-time matrix for interpolation later in the
    # trim_multiple events step
    if any('trim_multiple_events' in dict for dict in config['processing']):
        travel_time_df, catalog = create_travel_time_dataframe(
            streams, **config['travel_time'])

    window_conf = config['windows']
    model = TauPyModel(config['pickers']['travel_time']['model'])

    for st in streams:
        logging.debug('Checking stream %s...' % st.get_id())
        # Estimate noise/signal split time
        st = signal_split(
            st,
            origin,
            model,
            picker_config=config['pickers'],
            config=config)

        # Estimate end of signal
        end_conf = window_conf['signal_end']
        event_mag = origin.magnitude
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
    processing_steps = config['processing']

    # Loop over streams
    for stream in streams:
        logging.info('Stream: %s' % stream.get_id())
        for processing_step_dict in processing_steps:

            key_list = list(processing_step_dict.keys())
            if len(key_list) != 1:
                raise ValueError(
                    'Each processing step must contain exactly one key.')
            step_name = key_list[0]

            logging.debug('Processing step: %s' % step_name)
            step_args = processing_step_dict[step_name]
            # Using globals doesn't seem like a great solution here, but it
            # works.
            if step_name not in globals():
                raise ValueError(
                    'Processing step %s is not valid.' % step_name)

            # Origin is required by some steps and has to be handled specially.
            # There must be a better solution for this...
            if step_name in REQ_ORIGIN:
                step_args['origin'] = origin
            if step_name == 'trim_multiple_events':
                step_args['catalog'] = catalog
                step_args['travel_time_df'] = travel_time_df
            if step_name == 'compute_snr':
                step_args['mag'] = origin.magnitude

            if step_args is None:
                stream = globals()[step_name](stream)
            else:
                stream = globals()[step_name](stream, **step_args)

    # -------------------------------------------------------------------------
    # Begin colocated instrument selection
    colocated_conf = config['colocated']
    streams.select_colocated(**colocated_conf)

    for st in streams:
        for tr in st:
            tr.stats.standard.process_level = PROCESS_LEVELS['V2']

    logging.info('Finished processing streams.')
    return streams


def remove_response(st, f1, f2, f3=None, f4=None, water_level=None,
                    inv=None):
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
        inv (obspy.core.inventory.inventory):
            Obspy inventory object containing response information.

    Returns:
        StationStream: Instrument-response-corrected stream.
    """
    output = 'ACC'

    if inv is None:
        inv = st.getInventory()

    # Check if the response information is already attached in the trace stats
    for tr in st:

        # Check if this trace has already been converted to physical units
        if 'remove_response' in tr.getProvenanceKeys():
            logging.debug(
                'Trace has already had instrument response removed. '
                'Nothing to be done.')
            continue

        f_n = 0.5 / tr.stats.delta
        if f3 is None:
            f3 = 0.9 * f_n
        if f4 is None:
            f4 = f_n
        try:
            resp = inv.get_response(tr.id, tr.stats.starttime)
            paz = resp.get_paz()
            # Check if we have an instrument measuring velocity or accleration
            if tr.stats.channel[1] == 'H':
                # Attempting to remove instrument response can cause a variety
                # errors due to bad response metadata
                try:
                    # Note: rater than set output to 'ACC' we are are setting
                    # it to 'VEl" and then differentiating.
                    tr.remove_response(
                        inventory=inv, output='VEL', water_level=water_level,
                        pre_filt=(f1, f2, f3, f4), zero_mean=True, taper=False)
                    tr.differentiate()
                    tr.stats.standard.units = output.lower()
                    tr.stats.standard.process_level = PROCESS_LEVELS['V1']
                except BaseException as e:
                    reason = ('Encountered an error when attempting to remove '
                              'instrument response: %s' % str(e))
                    tr.fail(reason)
                    continue

                # Response removal can also result in NaN values due to bad
                # metadata, so check that data contains no NaN or inf values
                if not np.isfinite(tr.data).all():
                    reason = ('Non-finite values encountered after removing '
                              'instrument response.')
                    tr.fail(reason)
                    continue

                tr.data *= M_TO_CM  # Convert from m to cm
                tr.setProvenance(
                    'remove_response',
                    {
                        'method': 'remove_response',
                        'input_units': 'counts',
                        'output_units': ABBREV_UNITS[output],
                        'water_level': water_level,
                        'pre_filt_freqs': '%f, %f, %f, %f' % (f1, f2, f3, f4)
                    }
                )
            elif tr.stats.channel[1] == 'N':
                try:
                    # If no poles and zeros are present in the xml file,
                    # use the sensitivity method.
                    if len(paz.poles) == 0 and len(paz.zeros) == 0:
                        tr.remove_sensitivity(inventory=inv)
                        tr.data *= M_TO_CM  # Convert from m to cm
                        tr.stats.standard.units = output.lower()
                        tr.stats.standard.process_level = PROCESS_LEVELS['V1']
                        tr.setProvenance(
                            'remove_response',
                            {
                                'method': 'remove_sensitivity',
                                'input_units': 'counts',
                                'output_units': ABBREV_UNITS[output]
                            }
                        )
                    else:
                        tr.remove_response(
                            inventory=inv, output=output,
                            water_level=water_level,
                            zero_mean=True, taper=False
                        )
                        tr.data *= M_TO_CM  # Convert from m to cm
                        tr.stats.standard.units = output.lower()
                        tr.stats.standard.process_level = PROCESS_LEVELS['V1']
                        tr.setProvenance(
                            'remove_response',
                            {
                                'method': 'remove_response',
                                'input_units': 'counts',
                                'output_units': ABBREV_UNITS[output],
                                'water_level': water_level,
                                'pre_filt_freqs':
                                    '%f, %f, %f, %f' % (f1, f2, f3, f4)
                            }
                        )
                except BaseException as e:
                    reason = ('Encountered an error when attempting to remove '
                              'instrument sensitivity: %s' % str(e))
                    tr.fail(reason)
                    continue
            else:
                reason = ('This instrument type is not supported. '
                          'The instrument code must be either H '
                          '(high gain seismometer) or N (accelerometer).')
                tr.fail(reason)
        except BaseException as e:
            logging.info('Encountered an error when obtaining the poles and '
                         'zeros information: %s. Now using remove_sensitivity '
                         'instead of remove_response.' % str(e))
            tr.remove_sensitivity(inventory=inv)
            tr.data *= M_TO_CM  # Convert from m to cm
            tr.stats.standard.units = output.lower()
            tr.stats.standard.process_level = PROCESS_LEVELS['V1']
            tr.setProvenance(
                'remove_response',
                {
                    'method': 'remove_sensitivity',
                    'input_units': 'counts',
                    'output_units': ABBREV_UNITS[output]
                }
            )

    return st


def lowpass_max_frequency(st, fn_fac=0.9):
    """
    Cap lowpass corner as a fraction of the Nyquist.

    Args:
        st (StationStream):
            Stream of data.
        fn_fac (float):
            Factor to be multiplied by the Nyquist to cap the lowpass filter.

    Returns:
        StationStream: Resampled stream.
    """
    if not st.passed:
        return st

    for tr in st:
        fn = 0.5 * tr.stats.sampling_rate
        max_flp = fn * fn_fac
        freq_dict = tr.getParameter('corner_frequencies')
        if freq_dict['lowpass'] > max_flp:
            freq_dict['lowpass'] = max_flp
            tr.setParameter('corner_frequencies', freq_dict)

    return st


def min_sample_rate(st, min_sps=20.0):
    """
    Discard records if the sample rate doers not exceed minimum.

    Args:
        st (StationStream):
            Stream of data.
        min_sps (float):
            Minimum samples per second.

    Returns:
        StationStream: Stream checked for sample rate criteria.
    """
    if not st.passed:
        return st

    for tr in st:
        actual_sps = tr.stats.sampling_rate
        if actual_sps < min_sps:
            tr.fail('Minimum sample rate of %s not exceeded.' % min_sps)

    return st


def detrend(st, detrending_method=None):
    """
    Detrend stream.

    Args:
        st (StationStream):
            Stream of data.
        method (str): Method to detrend; valid options include the 'type'
            options supported by obspy.core.trace.Trace.detrend as well as:
                - 'baseline_sixth_order', which is for a baseline correction
                   method that fits a sixth-order polynomial to the
                   displacement time series, and sets the zeroth- and
                   first-order terms to be zero. The second derivative of the
                   fit polynomial is then removed from the acceleration time
                   series.
                - 'pre', for removing the mean of the pre-event noise window.

    Returns:
        StationStream: Detrended stream.
    """

    if not st.passed:
        return st

    for tr in st:
        if detrending_method == 'baseline_sixth_order':
            tr = _correct_baseline(tr)
        elif detrending_method == 'pre':
            tr = _detrend_pre_event_mean(tr)
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

    logging.debug('Setting corner frequencies...')
    if method == 'constant':
        st = corner_frequencies.get_constant(st, **constant)
    elif method == 'snr':
        st = corner_frequencies.get_snr(st, **snr)
        if snr['same_horiz'] and st.passed and st.num_horizontal > 1:
            lps = [tr.getParameter('corner_frequencies')[
                'lowpass'] for tr in st]
            hps = [tr.getParameter('corner_frequencies')[
                'highpass'] for tr in st]
            chs = [tr.stats.channel for tr in st]
            hlps = []
            hhps = []
            for i in range(len(chs)):
                if "z" not in chs[i].lower():
                    hlps.append(lps[i])
                    hhps.append(hps[i])
            llp = np.min(hlps)
            hhp = np.max(hhps)
            for i in range(len(chs)):
                if "z" not in chs[i].lower():
                    cfdict = st[i].getParameter('corner_frequencies')
                    cfdict['lowpass'] = llp
                    cfdict['highpass'] = hhp
                    st[i].setParameter('corner_frequencies', cfdict)
    else:
        raise ValueError("Corner frequency 'method' must be either "
                         "'constant' or 'snr'.")
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


def check_instrument(st, n_max=3, n_min=1, require_two_horiz=False):
    """
    Test the channels of the station.

    The purpose of the maximum limit is to skip over stations with muliple
    strong motion instruments, which can occur with downhole or structural
    arrays since our code currently is not able to reliably group by location
    within an array.

    The purpose of the minimum and require_two_horiz checks are to ensure the
    channels are required for subsequent intensity measures such as ROTD.

    Args:
        st (StationStream):
            Stream of data.
        n_max (int):
            Maximum allowed number of streams; default to 3.
        n_min (int):
            Minimum allowed number of streams; default to 1.
        require_two_horiz (bool):
            Require two horizontal components; default to `False`.

    Returns:
        Stream with adjusted failed fields.
    """
    if not st.passed:
        return st

    logging.debug('Starting check_instrument')
    logging.debug('len(st) = %s' % len(st))

    for failed_test, message in [
            (len(st) > n_max, 'More than %s traces in stream.' % n_max),
            (len(st) < n_min, 'Less than %s traces in stream.' % n_min),
            (require_two_horiz and (st.num_horizontal != 2),
             'Not two horizontal components')
    ]:
        if failed_test:
            for tr in st:
                tr.fail(message)
            # Stop at first failed test
            break

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
    logging.warning('This function is deprecated. Please replace with '
                    'check_instrument, which includes additional '
                    'functionality.')
    if not st.passed:
        return st

    logging.debug('Starting max_traces')
    logging.debug('len(st) = %s' % len(st))
    if len(st) > n_max:
        for tr in st:
            tr.fail('More than %s traces in stream.' % n_max)
    return st


def _detrend_pre_event_mean(trace):
    """
    Subtraces the mean of the pre-event noise window from the full trace.

    Args:
        trace (obspy.core.trace.Trace):
            Trace of strong motion data.

    Returns:
        trace: Detrended trace.
    """
    split_prov = trace.getParameter('signal_split')
    if isinstance(split_prov, list):
        split_prov = split_prov[0]
    split_time = split_prov['split_time']
    noise = trace.copy().trim(endtime=split_time)
    noise_mean = np.mean(noise.data)
    trace.data = trace.data - noise_mean
    return trace


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

    # Integrate twice to get the displacement time series
    disp_data = cumtrapz(cumtrapz(trace.data, dx=trace.stats.delta, initial=0),
                         dx=trace.stats.delta, initial=0)

    # Fit a sixth order polynomial to displacement time series, requiring
    # that the 1st and 0th order coefficients are zero
    time_values = np.linspace(
        0,
        trace.stats.npts - 1,
        trace.stats.npts) * trace.stats.delta
    poly_cofs = list(curve_fit(_poly_func, time_values, disp_data)[0])
    poly_cofs += [0, 0]

    # Construct a polynomial from the coefficients and compute
    # the second derivative
    polynomial = np.poly1d(poly_cofs)
    polynomial_second_derivative = np.polyder(polynomial, 2)

    # Subtract the second derivative of the polynomial from the
    # acceleration trace
    trace.data -= polynomial_second_derivative(time_values)
    trace.setParameter('baseline', {'polynomial_coefs': poly_cofs})

    return trace


def _poly_func(x, a, b, c, d, e):
    """
    Model polynomial function for polynomial baseline correction.
    """
    return a * x**6 + b * x**5 + c * x**4 + d * x**3 + e * x**2
