# stdlib imports
import warnings

# third party imports
import numpy as np
from numpy cimport ndarray
cimport numpy as np
cimport cython
from obspy.core.stream import Stream
from obspy.core.trace import Trace
from gmprocess.stationstream import StationStream
from gmprocess.stationtrace import StationTrace
from obspy.signal.invsim import corn_freq_2_paz, simulate_seismometer
from obspy import read

# local imports
from gmprocess.constants import GAL_TO_PCTG

cdef extern from "cfuncs.h":
    void calculate_spectrals_c(double *times, double *acc, int np,
                               double period, double damping, double *sacc,
                               double *svel, double *sdis);

cpdef list calculate_spectrals(np.ndarray[double, ndim=1, mode='c']times,
                               np.ndarray[double, ndim=1, mode='c']acc,
                               period, damping):
    """
    Returns a list of spectral responses for acceleration, velocity,
            and displacement.
    Args:
        times (np.ndarray): Times corresponding to the acceleration values.
        acceleration (np.ndarray): Acceleration values.
        period (float): Period in seconds.
        damping (float): Fraction of critical damping.

    Returns:
        list: List of spectral responses (np.ndarray).
    """
    cdef int kg = len(acc)
    cdef ndarray[double, ndim=1] spectral_acc = np.zeros(kg)
    cdef ndarray[double, ndim=1] spectral_vel = np.zeros(kg)
    cdef ndarray[double, ndim=1] spectral_dis = np.zeros(kg)

    calculate_spectrals_c(<double *>times.data, <double *>acc.data, kg,
                          period, damping,
                          <double *>spectral_acc.data,
                          <double *>spectral_vel.data,
                          <double *>spectral_dis.data)
    return [spectral_acc, spectral_vel, spectral_dis]


def get_acceleration(stream, units='%%g'):
    """
    Returns a stream of acceleration with specified units.
    Args:
        stream (obspy.core.stream.Stream): Strong motion timeseries
            for one station. With units of g (cm/s/s).
        units (str): Units of accelearation for output. Default is %g
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


def get_spectral(period, stream, damping=0.05, times=None):
    """
    Returns a stream of spectral response with units of %%g.
    Args:
        period (float): Period for spectral response.
        stream (obspy.core.stream.Stream): Strong motion timeseries
            for one station.
        damping (float): Damping of oscillator.
        times (np.ndarray): Array of times for the horizontal channels.
            Default is None.
    Returns:
        obpsy.core.stream.Stream or numpy.ndarray: stream of spectral response.
    """
    traces = []
    num_trace_range = range(len(stream))
    cdef int len_data = stream[0].data.shape[0]

    if isinstance(stream, (StationStream, Stream)):
        for idx in num_trace_range:
            trace = stream[idx]
            acc_sa = calculate_spectrals(trace.times(), trace.data,
                    period, damping)[0]
            stats = trace.stats.copy()
            stats['units'] = '%%g'
            acc_sa = np.array(acc_sa) * GAL_TO_PCTG
            spect_trace = StationTrace(data=acc_sa, header=stats)
            traces += [spect_trace]
        spect_stream = StationStream(traces)
        return spect_stream
    else:
        rotated = []
        for idx in range(0, len(stream)):
            rot_matrix = stream[idx]
            rotated_spectrals = np.zeros(rot_matrix.shape)
            for idy in range(0, len(rot_matrix)):
                acc_sa = np.asarray(calculate_spectrals(times, rot_matrix[idy],
                        period, damping)[0])
                acc_sa = acc_sa * GAL_TO_PCTG
                rotated_spectrals[idy] = acc_sa
            rotated += [rotated_spectrals]
        return rotated


def get_velocity(stream):
    """
    Returns a stream of velocity with units of cm/s.
    Args:
        stream (obspy.core.stream.Stream): Strong motion timeseries
            for one station.
    Returns:
        obpsy.core.stream.Stream: stream of velocity.
    """
    cdef int idx
    veloc_stream = Stream()
    for idx in range(len(stream)):
        trace = stream[idx]
        veloc_trace = trace.copy()
        veloc_trace.integrate()
        veloc_trace.stats['units'] = 'cm/s'
        veloc_stream.append(veloc_trace)
    return veloc_stream
