#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Local imports
from gmprocess.metrics.rotation.rotation import Rotation


class Null_Rotation(Rotation):
    """Class for null rotation calculation. This perfoms no action
    other than returning the input rotation_data."""

    def __init__(self, rotation_data, event=None):
        super().__init__(rotation_data, event=event)
        self.result = self.get_rotation_data()

    def get_rotation_data(self):
        """
        Returns:
            self.rotation_data: The original input without alteration.
        """
        return self.rotation_data
