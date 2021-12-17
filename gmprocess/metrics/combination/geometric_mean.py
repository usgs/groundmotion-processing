#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local imports
import numpy as np

# Third party imports
from gmprocess.metrics.combination.combination import Combination


class Geometric_Mean(Combination):
    """Class for calculation of geometric mean."""

    def __init__(self, combination_data):
        """
        Args:
            combination_data (dictionary or numpy.ndarray):
                Data for calculation.
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
            # This should be the case for any real trace data
            horizontals = self._get_horizontals()
            h1, h2 = horizontals[0], horizontals[1]
            if isinstance(h1, dict):
                # this is the case where IMT is FAS
                gm = {
                    "freqs": h1["freqs"],
                    "spectra": np.sqrt(h1["spectra"] * h2["spectra"]),
                }
            else:
                gm = {"": np.sqrt(h1 * h2)}
        else:
            # Just for tests?
            horizontals = self.combination_data
            time_freq = horizontals[0]
            h1, h2 = horizontals[1], horizontals[2]
            gm = [time_freq]
            gm += [np.sqrt(np.asarray(h1) * np.asarray(h2))]
        return gm
