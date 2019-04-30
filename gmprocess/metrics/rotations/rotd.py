from gmprocess.metrics.rotations.rotation import Rotation
from gmprocess.metrics.rotation import rotate


class Rotd(Rotation):
    """Class for computing the ROTD rotation."""
    def __init__(self, rotation_data,  origin=None):
        """
        Args:
            rotation_data (obspy.core.stream.Stream or numpy.ndarray): Intensity
                    measurement component.
            origin (obspy.core.event.Origin): Defines the focal time and
                    geographical location of an earthquake hypocenter.
                    Default is None.
        """
        super().__init__(rotation_data, origin=None)
        self.result = self.get_rotd()

    def get_rotd(self):
        """
        Performs GMROTD rotation.

        Returns:
            rotd: numpy.ndarray of the rotated and combined traces.
        """
        horizontals = self._get_horizontals()
        osc1, osc2 = horizontals[0].data, horizontals[1].data
        rotd = [rotate(osc1, osc2, combine=True)]
        return rotd
