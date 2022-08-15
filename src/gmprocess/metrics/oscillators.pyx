# stdlib imports
import warnings

# third party imports
import numpy as np
from numpy cimport ndarray
cimport numpy as np
cimport cython
from obspy.core.stream import Stream
from obspy.core.trace import Trace
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace
from obspy.signal.invsim import corn_freq_2_paz
from obspy import read

# local imports
from gmprocess.utils.constants import GAL_TO_PCTG

cdef extern from "cfuncs.h":
    void calculate_spectrals_c(double *acc, int npoints, double dt,
                               double period, double damping, double *sacc,
                               double *svel, double *sdis);

cpdef list calculate_spectrals(trace, period, damping):
    """
    Returns a list of spectral responses for acceleration, velocity,
            and displacement.
    Args:
        trace (StationTrace):
            The trace to be acted upon
        period (float):
            Period in seconds.
        damping (float):
            Fraction of critical damping.
    Returns:
        list: List of spectral responses (np.ndarray).
    """
    cdef int new_np = trace.stats.npts
    cdef double new_dt = trace.stats.delta
    cdef double new_sample_rate = trace.stats.sampling_rate
    # The time length of the trace in seconds
    cdef double tlen = (new_np - 1) * new_dt
    cdef int ns

    # This is the resample factor for low-sample-rate/high-frequency
    ns = (int)(10. * new_dt / period - 0.01) + 1
    if ns > 1:
        # Increase the number of samples as necessary
        new_np = new_np * ns
        # Make the new number of samples a power of two
        # leaving this out for now; it slows things down but doesn't
        # appear to affect the results. YMMV.
        # new_np = 1 if new_np == 0 else 2**(new_np - 1).bit_length()
        # The new sample interval
        new_dt = tlen / (new_np - 1)
        # The new sample rate
        new_sample_rate = 1.0 / new_dt
        # Make a copy because resampling happens in place
        trace = trace.copy()
        # Resample the trace
        trace.resample(new_sample_rate, window=None)

    cdef ndarray[double, ndim=1] spectral_acc = np.zeros(new_np)
    cdef ndarray[double, ndim=1] spectral_vel = np.zeros(new_np)
    cdef ndarray[double, ndim=1] spectral_dis = np.zeros(new_np)
    cdef ndarray[double, ndim=1] acc = trace.data

    calculate_spectrals_c(<double *>acc.data, new_np, new_dt,
                          period, damping,
                          <double *>spectral_acc.data,
                          <double *>spectral_vel.data,
                          <double *>spectral_dis.data)
    return [spectral_acc, spectral_vel, spectral_dis, new_np, new_dt,
            new_sample_rate]


def get_acceleration(stream, units='%%g'):
    """
    Returns a stream of acceleration with specified units.

    Args:
        stream (obspy.core.stream.Stream):
            Strong motion timeseries for one station. With units of g (cm/s/s).
        units (str):
            Units of accelearation for output. Default is %g.

    Returns:
        obpsy.core.stream.Stream: stream of acceleration.
    """
    cdef int idx
    accel_stream = Stream()
    for idx in range(len(stream)):
        trace = stream[idx]
        accel_trace = trace.copy()
        if units == '%%g':
            accel_trace.data = trace.data * GAL_TO_PCTG
            accel_trace.stats['units'] = '%%g'
        elif units == 'm/s/s':
            accel_trace.data = trace.data * 0.01
            accel_trace.stats['units'] = 'm/s/s'
        else:
            accel_trace.data = trace.data
            accel_trace.stats['units'] = 'cm/s/s'
        accel_stream.append(accel_trace)
    return accel_stream


def get_spectral(period, stream, damping=0.05, times=None, config=None):
    """
    Returns a stream of spectral response with units of %%g.

    Args:
        period (float):
            Period for spectral response.
        stream (StationStream):
            Strong motion timeseries for one station.
        damping (float):
            Damping of oscillator.
        times (np.ndarray):
            Array of times for the horizontal channels. Default is None.
        config (dict):
            StationStream.

    Returns:
        StationStream.
    """
    cdef int len_data = stream[0].data.shape[0]

    # Use as-recorded or upsampled record?
    use_upsampled = False
    dt = stream[0].stats.delta
    ns = (int)(10. * dt / period - 0.01) + 1
    if ns > 1:
        use_upsampled = True
        dt = stream[0].getCached('upsampled')['dt']

    if 'rotated' in stream.getStreamParamKeys():
        # For ROTD and GMROTD
        rotated = []
        if use_upsampled:
            rotated_data = stream.getStreamParam('upsampled_rotated')
        else:
            rotated_data = stream.getStreamParam('rotated')

        for idx in range(len(rotated_data)):
            rot_matrix = rotated_data[idx]
            rotated_spectrals = []
            # This is the loop over rotation angles
            for idy in range(0, len(rot_matrix)):
                stats = {
                    'npts': len(rot_matrix[idy]),
                    'delta': dt,
                    'sampling_rate': 1.0 / dt
                }
                new_trace = Trace(data=rot_matrix[idy], header=stats)
                sa_list = calculate_spectrals(new_trace, period, damping)
                acc_sa = sa_list[0]
                acc_sa *= GAL_TO_PCTG
                rotated_spectrals.append(acc_sa)
            rotated += [rotated_spectrals]

        # Add rotated data to stream parameters
        stream.setStreamParam('rotated_oscillator', rotated)
        return stream
    else:
        traces = []
        # For anything but ROTD and GMROTD
        for idx in range(len(stream)):
            trace = stream[idx]
            if use_upsampled:
                trace_dict = stream[idx].getCached('upsampled')
                stats = {
                    'npts': trace_dict['np'],
                    'delta': dt,
                    'sampling_rate': 1.0 / dt
                }
                temp_trace = Trace(data=trace_dict['data'], header=stats)
            else:
                temp_trace = trace
            sa_list = calculate_spectrals(temp_trace, period, damping)
            acc_sa = sa_list[0]
            acc_sa *= GAL_TO_PCTG
            stats = trace.stats.copy()
            stats.npts = sa_list[3]
            stats.delta = sa_list[4]
            stats.sampling_rate = sa_list[5]
            stats['units'] = '%%g'
            spect_trace = StationTrace(data=acc_sa, header=stats, config=config)
            traces += [spect_trace]
        spect_stream = StationStream(traces)
        return spect_stream
