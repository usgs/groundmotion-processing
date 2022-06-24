#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local imports
import numpy as np

# Third party imports
from gmprocess.metrics.combination.combination import Combination


class Quadratic_Mean(Combination):
    """Class for calculation of quadratic mean."""

    def __init__(self, combination_data):
        """
        Args:
            combination_data (dictionary or numpy.ndarray):
                Data for calculation.
        """
        super().__init__(combination_data)
        self.result = self.get_quadratic_mean()

    def get_quadratic_mean(self):
        """
        Performs calculation of quadratic mean.

        Returns:
            gm: Dictionary of quadratic mean.
        """
        if isinstance(self.combination_data, dict):
            # This should be the case for any real trace data
            horizontals = self._get_horizontals()
            h1, h2 = horizontals[0], horizontals[1]
            if isinstance(h1, dict):
                # this is the case where IMT is FAS
                qm = {
                    "freqs": h1["freqs"],
                    "spectra": np.sqrt((h1["spectra"] ** 2 + h2["spectra"] ** 2) / 2),
                }
            else:
                qm = {"": np.sqrt(np.mean([h1 ** 2, h2 ** 2]))}
        else:
            # Just for tests?
            horizontals = self.combination_data
            time_freq = horizontals[0]
            h1, h2 = horizontals[1], horizontals[2]
            qm = [time_freq]
            qm += [np.sqrt(np.mean([np.abs(trace) ** 2 for trace in [h1, h2]], axis=0))]
        return qm
