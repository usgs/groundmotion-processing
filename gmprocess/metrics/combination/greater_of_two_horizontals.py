#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gmprocess.metrics.combination.combination import Combination
import numpy as np


class Greater_Of_Two_Horizontals(Combination):
    """Class for extracting the maximum value between the two horizontal
    channels."""

    def __init__(self, combination_data):
        """
        Args:
            combination_data (dictionary): Data for calculation.
        """
        super().__init__(combination_data)
        self.result = self.get_greater_of_two_horizontals()

    def get_greater_of_two_horizontals(self):
        """
        Picks the greater value between two horizontal channels.

        Returns:
            g2h: Dictionary of greater of two horizontals.
        """
        horizontals = self._get_horizontals()
        h1, h2 = horizontals[0], horizontals[1]
        g2h = {"": np.abs(max([h1, h2]))}
        return g2h
