# Local imports
from gmprocess.metrics.exception import PGMException


class Rotation(object):
    """Base class for rotation calculations."""
    def __init__(self, rotation_data, origin=None):
        """
        Args:
            rotation_data (obspy.core.stream.Stream or numpy.ndarray): Intensity
                    measurement component.
            origin (obspy.core.event.Origin): Defines the focal time and
                    geographical location of an earthquake hypocenter.
                    Default is None.
        """
        self.rotation_data = rotation_data

    def _get_horizontals(self):
        """
        Gets the two horizontal components.

        Returns:
            horizontal_channels: list of horizontal channels
                    (obspy.core.trac.Trace).

        Raises:
            PGMException: if there are less than or greater than two
                    horizontal channels.
        """
        horizontal_channels = []
        for trace in self.rotation_data:
            # Group all of the max values from traces without
            # Z in the channel name
            if 'Z' not in trace.stats['channel'].upper():
                horizontal_channels += [trace.copy()]
        ## Test the horizontals
        if len(horizontal_channels) > 2:
            raise PGMException('Rotation: More than two horizontal channels.')
        elif len(horizontal_channels) < 2:
            raise PGMException('Rotation: Less than two horizontal channels.')
        elif len(horizontal_channels[0].data) != len(horizontal_channels[1].data):
            raise PGMException('Rotation: Horizontal channels have different lengths.')
        return horizontal_channels
