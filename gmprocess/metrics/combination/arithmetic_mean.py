# Local imports
import numpy as np

# Third party imports
from gmprocess.metrics.combination.combination import Combination


class Arithmetic_Mean(Combination):
    """Class for calculation of arithmetic mean."""
    def __init__(self, combination_data):
        """
        Args:
            combination_data (dictionary): Data for calculation.
        """
        super().__init__(combination_data)
        self.result = self.get_arithmetic_mean()

    def get_arithmetic_mean(self):
        """
        Performs calculation of arithmetic mean.

        Returns:
            am: Dictionary of arithmetic mean.
        """
        if isinstance(self.combination_data, dict):
            horizontals = self._get_horizontals()
            h1, h2 = horizontals[0], horizontals[1]
            am = {'': 0.5 * (h1 + h1)}
        else:
            horizontals = self.combination_data
            time_freq = horizontals[0]
            h1, h2 = horizontals[1], horizontals[2]
            am = [time_freq]
            am += [np.mean([h1, h2], axis=0)]
        return am
