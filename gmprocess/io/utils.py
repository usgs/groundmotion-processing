# third party imports
import numpy as np

# local imports
from gmprocess.config import get_config

CONFIG = get_config()


def is_evenly_spaced(times, decimal_tolerance):
    """
    Checks whether times are evenly spaced.

    Args:
        times (array):
            Array of floats of times in seconds.
        decimal_tolerance (int):
            Decimal tolerance for testing equality of time deltas.

    Returns:
        bool: True if times are evenly spaced. False otherwise.
    """
    diffs = np.diff(times).round(decimals=decimal_tolerance)
    if len(np.unique(diffs)) > 1:
        return False
    else:
        return True


def resample_uneven_trace(trace, times, data, resample_rate=None,
                          method='linear'):
    """
    Resample unevenly spaced data.

    Args:
        trace (gmprocess.stationtrace.StationTrace):
            Trace to resample.
        times (array):
            Array of floats of times in seconds.
        data (array):
            Array of floats of values to be resampled.
        resample_rate (float):
            Resampling rate in Hz.
        method (str):
            Method of resampling. Currently only supported is 'linear'.

    Returns:
        trace (gmprocess.stationtrace.StationTrace):
            Resampled trace with updated provenance information.
    """
    npts = len(times)
    duration = times[-1] - times[0]
    nominal_sps = (npts - 1) / duration

    # Load the resampling rate from the config if not provided
    if resample_rate is None:
        resample_rate = CONFIG['read']['resample_rate']

    new_times = np.arange(times[0], times[-1], 1 / resample_rate)

    if method == 'linear':
        trace.data = np.interp(new_times, times, data, np.nan, np.nan)
        trace.stats.sampling_rate = resample_rate
        method_str = 'Linear interpolation of unevenly spaced samples'
    else:
        raise ValueError('Unsupported method value.')

    trace.setProvenance('resample', {'record_length': duration,
                                     'total_no_samples': npts,
                                     'nominal_sps': nominal_sps,
                                     'method': method_str})

    return trace
