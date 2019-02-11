# local imports
from gmprocess.metrics.exception import PGMException
from gmprocess.metrics.rotation import get_max, rotate


def calculate_gmrotd(stream, percentiles, rotated=False, **kwargs):
    """
    Rotate two horizontal channels using the geometric mean.
    Args:
        stream (obspy.core.stream.Stream or list): stream of oscillators or
            list of rotation matrices.
        percentiles (list): list of percentiles (float).
            Example: [100, 50, 75] results in RotD100, RotD50, RotD75.
        rotated (bool): Wheter the stream is a rotation matrix. Used by the
                arias intensity calculation. Default is False.
    Returns:
        dictionary: Dictionary of geometric mean for each percentile.
    """
    if rotated:
        gm_percentiles = get_max(stream[0], 'gm', stream[1], percentiles)[1]
        gmrotd_dict = {}
        for idx, percent in enumerate(percentiles):
            gmrotd_dict[percent] = gm_percentiles[idx]
    else:
        horizontals = _get_horizontals(stream)
        if len(horizontals) > 2:
            raise PGMException('More than two horizontal channels.')
        elif len(horizontals) < 2:
            raise PGMException('Less than two horizontal channels.')
        osc1, osc2 = horizontals[0].data, horizontals[1].data
        if len(osc1) != len(osc2):
            raise PGMException('Horizontal channels have different lengths.')

        osc1_rot, osc2_rot = rotate(osc1, osc2, combine=False)
        gm_percentiles = get_max(osc1_rot, 'gm', osc2_rot, percentiles)[1]

        gmrotd_dict = {}
        for idx, percent in enumerate(percentiles):
            gmrotd_dict[percent] = gm_percentiles[idx]
    return gmrotd_dict


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
    for _, trace in enumerate(stream):
        # Group all of the max values from traces without
        # Z in the channel name
        if 'Z' not in trace.stats['channel'].upper():
            horizontal_channels += [trace.copy()]
    return horizontal_channels
