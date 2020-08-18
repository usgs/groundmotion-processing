# Local imports
from gmprocess.metrics.transform.transform import Transform


class Null_Transform(Transform):
    """"Class for null transform calculation. This perfoms no action
            other than returning the input transform_data."""

    def __init__(self, transform_data, damping=None, period=None, times=None,
                 max_period=None):
        super().__init__(transform_data, damping=None, period=None, times=None,
                         max_period=None)
        self.result = self.get_transform_data()

    def get_transform_data(self):
        """
        Returns:
            self.transform_data: The original input without alteration.
        """
        return self.transform_data
