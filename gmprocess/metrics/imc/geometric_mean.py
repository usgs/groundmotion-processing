# third party imports
import numpy as np

# local imports
from gmprocess.metrics.exception import PGMException


def calculate_geometric_mean(stream, return_combined=False, **kwargs):
    """Return GREATER_OF_TWO_HORIZONTALS value for given input Stream.

    NB: The input Stream should have already been "processed",
    i.e., filtered, detrended, tapered, etc.)

    Args:
        stream (Obspy Stream): Stream containing one or Traces of
            acceleration data in gals.
        kwargs (**args): Ignored by this class.

    Returns:
        float: GREATER_OF_TWO_HORIZONTALS (float).
    """
    gm_data = _gm_combine(stream)
    if return_combined:
        return gm_data
    else:
        return np.max(gm_data)


def _gm_combine(stream):
    horizontals = []
    for trace in stream:
        # Group all of the max values from traces without
        # Z in the channel name
        if 'Z' not in trace.stats['channel'].upper():
            horizontals += [trace]
    if len(horizontals) > 2:
        raise PGMException('More than two horizontal channels.')
    elif len(horizontals) < 2:
        raise PGMException('Less than two horizontal channels.')

    if len(horizontals[0].data) != len(horizontals[1].data):
        raise PGMException('Horizontal channels are not the same length.')
    if horizontals[0].stats.sampling_rate != horizontals[1].stats.sampling_rate:
        raise PGMException('Horizontal channels have different sampling rates.')

    geometric_means = np.sqrt(np.mean(
    [np.abs(trace.data)**2 for trace in horizontals], axis=0))
    return geometric_means
