#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local imports
from gmprocess.metrics.transform.transform import Transform


class Null_Transform(Transform):
    """"Class for null transform calculation. This perfoms no action
            other than returning the input transform_data."""

    def __init__(self, transform_data, damping=None, period=None, times=None,
                 max_period=None, allow_nans=None, bandwidth=None, config=None):
        super().__init__(transform_data, damping=None, period=None, times=None,
                         max_period=None, allow_nans=None, bandwidth=None,
                         config=None)
        self.result = self.get_transform_data()

    def get_transform_data(self):
        """
        Returns:
            self.transform_data: The original input without alteration.
        """
        return self.transform_data
