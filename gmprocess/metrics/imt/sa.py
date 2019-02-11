# stdlib imports
import logging

# local imports
from gmprocess.metrics.exception import PGMException
from gmprocess.metrics.gather import get_pgm_classes, group_imcs


def calculate_sa(stream, imcs, rotation_matrix=None):
    """
    Calculate the peak ground acceleration.

    Args:
        stream (obspy.core.stream.Stream): streams of strong ground motion.
            Traces in stream must be in units of %%g.
        imcs (list): list of imcs.
        rotation_matrix (ndarray): A rotation matrix for the rotd component.
            This is required when the rotd component is requested.

    Returns:
        dictionary: Dictionary of sa for different components.
    """
    sa_dict = {}
    # check units and add channel pga
    for trace in stream:
        if trace.stats['units'] != '%%g':
            raise PGMException('Invalid units for sa: %r. '
                               'Units must be %%g' % trace.stats['units'])
    grouped_imcs = group_imcs(imcs)
    # gather imc classes
    pgm_classes = get_pgm_classes('imc')
    # store sa for imcs
    for imc in grouped_imcs:
        if 'calculate_' + imc in pgm_classes:
            sa_func = pgm_classes['calculate_' + imc]
            sa = sa_func(stream, percentiles=grouped_imcs[imc])
            if imc == 'rotd':
                if rotation_matrix is None:
                    raise PGMException(
                        'The rotation matrix must be included '
                        'in order to calculate the rotd component.')
                sa = sa_func(rotation_matrix, percentiles=grouped_imcs[imc],
                             rotated=True)
                for percentile in sa:
                    sa_dict[imc.upper() + str(percentile)] = sa[percentile]
            elif imc.find('rot') >= 0:
                for percentile in sa:
                    sa_dict[imc.upper() + str(percentile)] = sa[percentile]
            elif imc.find('channels') >= 0:
                for channel in sa:
                    sa_dict[channel] = sa[channel]
            else:
                sa_dict[imc.upper()] = sa
        else:
            logging.warning('Not a valid IMC: %r. Skipping...' % imc)
    return sa_dict
