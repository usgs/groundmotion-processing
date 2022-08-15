#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local imports
from gmprocess.metrics.combination.combination import Combination


class Null_Combination(Combination):
    """Class for null combination calculation. This perfoms no action
    other than returning the input combination_data.
    """

    def __init__(self, combination_data):
        """
        Args:
            combination_data (dictionary):
                Data for calculation.
        """
        super().__init__(combination_data)
        self.result = self.get_combination_data()

    def get_combination_data(self):
        """
        Returns:
            self.combination_data: The original input without alteration.
        """
        return self.combination_data
