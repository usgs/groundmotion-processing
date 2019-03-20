# stdlib imports
import logging

# local imports
from gmprocess.metrics.exception import PGMException
from gmprocess.metrics.gather import get_pgm_classes, group_imcs


def calculate_pga(stream, imcs, origin=None):
    """
    Calculate the peak ground acceleration.

    Args:
        stream (obspy.core.stream.Stream): streams of strong ground motion.
            Traces in stream must be in units of %%g.
        imcs (list): list of imcs.
        origin (obspy.core.event.origin.Origin):
            Obspy event origin object.

    Returns:
        dictionary: Dictionary of pga for different components.
    """
    pga_dict = {}
    # check units and add channel pga
    for trace in stream:
        if trace.stats['units'] != '%%g':
            raise PGMException('Invalid units for PGA: %r. '
                               'Units must be %%g' % trace.stats['units'])
    # sort imcs
    grouped_imcs = group_imcs(imcs)
    # gather imc classes
    pgm_classes = get_pgm_classes('imc')
    # store pga for imcs
    for imc in grouped_imcs:
        if 'calculate_' + imc in pgm_classes:
            pga_func = pgm_classes['calculate_' + imc]
            pga = pga_func(stream, origin=origin,
                           percentiles=grouped_imcs[imc])
            if imc.find('rot') >= 0:
                for percentile in pga:
                    pga_dict[imc.upper() + str(percentile)] = pga[percentile]
            elif imc.find('channels') >= 0:
                for channel in pga:
                    pga_dict[channel] = pga[channel]
            elif imc.find('radial_transverse') >= 0:
                for channel in pga:
                    pga_dict[channel] = pga[channel]
            else:
                pga_dict[imc.upper()] = pga
        else:
            logging.warning('Not a valid IMC: %r. Skipping...' % imc)
    return pga_dict
