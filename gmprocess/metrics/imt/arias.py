import logging

# third party imports
import numpy as np
from scipy import integrate
import scipy.constants as sp
from obspy.core.trace import Trace
from obspy.core.stream import Stream

# local imports
from gmprocess.metrics.exception import PGMException
from gmprocess.metrics.gather import get_pgm_classes, group_imcs
from gmprocess.metrics.rotation import rotate


def calculate_arias(stream, imcs, return_streams=False, origin=None):
    """
    Calculate the peak ground acceleration.
    Args:
        stream (obspy.core.stream.Stream): streams of strong ground motion.
            Traces in stream must be in units of m/s/s.
        imcs (list): list of imcs.
        osccillators (dictionary): Dictionary of oscillators. Used when
                rotation imcs are requested. Default is None.
        return_streams (bool): Whether to return streams.
        origin (obspy.core.event.origin.Origin):
            Obspy event origin object.
    Returns:
        dictionary: Dictionary of arias for different components.
    """
    arias_streams = _calculate_channel_arias(stream)
    arias_stream = arias_streams[0]
    normalized_stream = arias_streams[1]

    if return_streams:
        return (arias_stream, normalized_stream)

    arias_dict = {}
    # sort imcs
    grouped_imcs = group_imcs(imcs)

    # gather imc classes
    pgm_classes = get_pgm_classes('imc')
    # store arias for imcss

    for imc in grouped_imcs:
        arias_func = pgm_classes['calculate_' + imc]
        if 'calculate_' + imc in pgm_classes:
            if imc.find('gmrot') >= 0:
                Ia, NIa = _calculate_rotated_arias(stream, 'gm')
                arias = arias_func(Ia, percentiles=grouped_imcs[imc],
                                   rotated=True, origin=origin)
                for percentile in arias:
                    arias_dict[imc.upper() + str(percentile)
                               ] = arias[percentile]
            elif imc.find('rot') >= 0:
                Ia, NIa = _calculate_rotated_arias(stream, 'nongm')
                arias = arias_func(Ia, percentiles=grouped_imcs[imc],
                                   rotated=True, origin=origin)
                for percentile in arias:
                    arias_dict[imc.upper() + str(percentile)
                               ] = arias[percentile]
            elif imc.find('channels') >= 0:
                arias = arias_func(arias_stream, origin=origin)
                for channel in arias:
                    arias_dict[channel] = arias[channel]
            else:
                arias = arias_func(arias_stream, origin=origin)
                arias_dict[imc.upper()] = arias
        else:
            logging.warning('Not a valid IMC: %r. Skipping...' % imc)
    return arias_dict


def _calculate_rotated_arias(stream, rotation):
    """Calculates Arias Intensity.
    Args:
        stream (obspy.core.stream.Stream): Stream of acceleration values
                in m/s/s.
        rotation (str): Type of rotation. gm or nongm.
    Returns:
        Ia (list): list of rotation matrices of Arias intensity values
                in m/s with respect to time.
        NIa (list): list of rotation matrices of normalized Arias intensity
                values with respect to time.
    Raises:
        PGMException: If the units are not valid. Units must be m/s/s. If two
                horizontal components are not available. If time delta is not
                the same for all horizontal traces.
    """
    horizontals = []
    for trace in stream:
        if trace.stats['units'] != 'm/s/s':
            raise PGMException('Invalid units for ARIAS: %r. '
                               'Units must be m/s/s' % trace.stats['units'])
        if trace.stats['channel'].upper().find('Z') < 0:
            horizontals += [trace.copy()]
    if len(horizontals) != 2:
        PGMException('Two horizontal channels are not available. Rotation '
                     'cannot be performed.')
    dt = horizontals[0].stats['delta']
    g = sp.g
    if rotation == 'nongm':
        rot = [rotate(horizontals[0], horizontals[1], combine=True)]
    elif rotation == 'gm':
        rot1, rot2 = rotate(horizontals[0], horizontals[1], combine=False)
        rot = [rot1, rot2]
    NIa = []
    Ia = []
    for channel in rot:
        for idx, rot_degree in enumerate(channel):
            acc2 = rot_degree
            # Calculate Arias intensity
            integration = integrate.cumtrapz(acc2 * acc2, dx=dt)
            arias_intensity = integration * np.pi / (2 * g)

            # Calculate normalized Arias intensity
            # divide arias intensity by its max value
            norm_arias_intensity = arias_intensity / np.amax(arias_intensity)

            if idx == 0:
                rotated_ia = [arias_intensity]
                rotated_nia = [norm_arias_intensity]
            else:
                rotated_ia = np.append(rotated_ia, [arias_intensity], axis=0)
                rotated_nia = np.append(rotated_nia,
                                        [norm_arias_intensity], axis=0)
        NIa += [rotated_nia]
        Ia += [rotated_ia]
    return(Ia, NIa)


def _calculate_channel_arias(stream):
    """Calculates Arias Intensity.
    Args:
        stream (obspy.core.stream.Stream): Stream of acceleration values
                in m/s/s.
    Returns:
        Ia (obspy.core.stream.Stream): Stream of Arias intensity values
                in m/s with respect to time.
        NIa (obspy.core.stream.Stream): Stream of normalized Arias intensity
                values with respect to time.
    Raises:
        PGMException: If the units are not valid. Units must be m/s/s.
    """
    Ia = Stream()
    NIa = Stream()
    for trace in stream:
        if trace.stats['units'] != 'm/s/s':
            raise PGMException('Invalid units for ARIAS: %r. '
                               'Units must be m/s/s' % trace.stats['units'])
        dt = trace.stats['delta']
        g = sp.g
        acc2 = trace.data

        # Calculate Arias intensity
        integration = integrate.cumtrapz(acc2 * acc2, dx=dt)
        arias_intensity = integration * np.pi / (2 * g)

        # Calculate normalized Arias intensity
        # divide arias intensity by its max value
        norm_arias_intensity = arias_intensity / np.amax(arias_intensity)
        stats_out = trace.stats.copy()
        stats_out['units'] = 'm/s'
        trace_ia = Trace(data=arias_intensity, header=stats_out)
        trace_nia = Trace(data=norm_arias_intensity, header=stats_out)
        Ia.append(trace_ia)
        NIa.append(trace_nia)
    return(Ia, NIa)
