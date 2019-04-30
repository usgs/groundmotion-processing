# Local imports
import numpy as np

# Third party imports
from gmprocess.metrics.combination.combination import Combination


class AM(Combination):
    """Class for calculation of arithmetic mean."""
    def __init__(self, combination_data):
        """
        Args:
            combination_data (dictionary): Data for calculation.
        """
        super().__init__(combination_data)
        self.result = self.get_am()

    def get_am(self):
        """
        Performs calculation of arithmetic mean.

        Returns:
            am: Dictionary of arithmetic mean.
        """
        if isinstance(self.combination_data, dict):
            horizontals = self._get_horizontals()
            h1, h2 = horizontals[0], horizontals[1]
            am = {'': 0.5 * (h1 + h1)}
        return am
