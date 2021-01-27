# Local imports
from gmprocess.metrics.transform.transform import Transform
from gmprocess.stationstream import StationStream
from gmprocess.stationtrace import StationTrace


class Integrate(Transform):
    """Class for computing the integral."""
    def __init__(self, transform_data, damping=None, period=None, times=None):
        """
        Args:
            transform_data (obspy.core.stream.Stream or numpy.ndarray): Intensity
                    measurement component.
            damping (float): Damping for spectral amplitude calculations.
                    Default is None.
            period (float): Period for spectral amplitude calculations.
                    Default is None.
            times (numpy.ndarray): Times for the spectral amplitude calculations.
                    Default is None.
        """
        super().__init__(transform_data, damping=None, period=None, times=None)
        self.result = self.get_integral()

    def get_integral(self):
        """
        Calculated the integral of each trace's data.

        Returns:
            stream: StationStream with the integrated data.
        """
        stream = StationStream([])
        for trace in self.transform_data:
            integrated_trace = trace.copy().integrate()
            if integrated_trace.stats.standard.units == 'acc':
                integrated_trace.stats.standard.units = 'vel'
            elif integrated_trace.stats.standard.units == 'vel':
                integrated_trace.stats.standard.units = 'disp'
            stream.append(integrated_trace)
        return stream
