# Local imports
import numpy as np

# Third party imports
from gmprocess.metrics.combination.combination import Combination


class Geometric_Mean(Combination):
    """Class for calculation of geometric mean."""
    def __init__(self, combination_data):
        """
        Args:
            combination_data (dictionary or numpy.ndarray): Data for calculation.
        """
        super().__init__(combination_data)
        self.result = self.get_geometric_mean()

    def get_geometric_mean(self):
        """
        Performs calculation of geometric mean.

        Returns:
            gm: Dictionary of geometric mean.
        """
        if isinstance(self.combination_data, dict):
            horizontals = self._get_horizontals()
            h1, h2 = horizontals[0], horizontals[1]
            gm = {'' : np.sqrt(h1 * h1)}
        else:
            horizontals = self.combination_data
            time_freq = horizontals[0]
            h1, h2 = horizontals[1], horizontals[2]
            gm = [time_freq]
            gm += [np.sqrt(np.asarray(h1)*np.asarray(h2))]
        return gm
