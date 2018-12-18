# third party imports
from gmprocess.metrics.exception import PGMException
from gmprocess.metrics.rotation import get_max, rotate


def calculate_rotd(stream, percentiles, rotated=False, **kwargs):
    """
    Rotate two horizontal channels and combine to get the spectral response.

    Args:
        stream (obspy.core.stream.Stream): stream of oscillators.
        percentiles (list): list of percentiles (float).
            Example: [100, 50, 75] results in RotD100, RotD50, RotD75.
        rotated (bool): Wheter the stream is a rotation matrix. Used by
                the arias intensity calculation. Default is False.

    Returns:
        dictionary: Dictionary of oienation indeendent nongeometric mean
            measures for each percentile.
    """
    if rotated == True:
        rot_percentiles = get_max(stream[0], 'max', percentiles=percentiles)[1]
        rotd_dict = {}
        for idx, percent in enumerate(percentiles):
            rotd_dict[percent] = rot_percentiles[idx]
    else:
        horizontals = _get_horizontals(stream)
        if len(horizontals) > 2:
            raise PGMException('More than two horizontal channels.')
        elif len(horizontals) < 2:
            raise PGMException('Less than two horizontal channels.')
        osc1, osc2 = horizontals[0].data, horizontals[1].data
        if len(osc1) != len(osc2):
            raise PGMException('Horizontal channels have different lengths.')

        rot = rotate(osc1, osc2, combine=True)
        rot_percentiles = get_max(rot, 'max', None, percentiles)[1]

        rotd_dict = {}
        for idx, percent in enumerate(percentiles):
            rotd_dict[percent] = rot_percentiles[idx]
    return rotd_dict


def _get_horizontals(stream):
    """
    Gets the two horizontal components

    Args:
        stream (obspy.core.stream.Stream): Strong motion timeseries
            for one station.

    Returns:
        list: list of horizontal channels (obspy.core.trac.Trace)
    """
    horizontal_channels = []
    for trace in stream:
        # Group all of the max values from traces without
        # Z in the channel name
        if 'Z' not in trace.stats['channel'].upper():
            horizontal_channels += [trace.copy()]
    return horizontal_channels
