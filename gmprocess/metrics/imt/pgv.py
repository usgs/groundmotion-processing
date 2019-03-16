# stdlib imports
import logging

# local imports
from gmprocess.metrics.exception import PGMException
from gmprocess.metrics.gather import get_pgm_classes, group_imcs


def calculate_pgv(stream, imcs, origin=None):
    """
    Calculate the peak ground velocity.

    Args:
        stream (obspy.core.stream.Stream): streams of strong ground motion.
            Traces in stream must be in units of cm/s.
        imcs (list): list of imcs.
        origin (obspy.core.event.origin.Origin):
            Obspy event origin object.

    Returns:
        dictionary: Dictionary of pgv for different components.
    """
    pgv_dict = {}
    # check units and add channel pga
    for trace in stream:
        if trace.stats['units'] != 'cm/s':
            raise PGMException('Invalid units for PGV: %r. '
                               'Units must be cm/s' % trace.stats['units'])
    grouped_imcs = group_imcs(imcs)
    # gather imc classes
    pgm_classes = get_pgm_classes('imc')
    # store pgv for imcs
    for imc in grouped_imcs:
        if 'calculate_' + imc in pgm_classes:
            pgv_func = pgm_classes['calculate_' + imc]
            pgv = pgv_func(stream, origin=origin,
                           percentiles=grouped_imcs[imc])
            if imc.find('rot') >= 0:
                for percentile in pgv:
                    pgv_dict[imc.upper() + str(percentile)] = pgv[percentile]
            elif imc.find('channels') >= 0:
                for channel in pgv:
                    pgv_dict[channel] = pgv[channel]
            else:
                pgv_dict[imc.upper()] = pgv
        else:
            logging.warning('Not a valid IMC: %r. Skipping...' % imc)
    return pgv_dict
