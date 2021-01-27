# Third party imports
import numpy as np
from obspy import Stream

# Local imports
from gmprocess.metrics.reduction.reduction import Reduction
from gmprocess.stationstream import StationStream


class Max(Reduction):
    """Class for calculation of maximum value."""

    def __init__(self, reduction_data, bandwidth=None, percentile=None,
                 period=None, smoothing=None):
        """
        Args:
            reduction_data (obspy.core.stream.Stream or numpy.ndarray):
                Intensity measurement component.
            percentile (float):
                Percentile for rotation calculations. Default is None.
            period (float):
                Period for smoothing (Fourier amplitude spectra) calculations.
                Default is None.
            smoothing (string):
                Smoothing type. Default is None.
            bandwidth (float):
                Bandwidth for the smoothing operation. Default is None.
        """
        super().__init__(reduction_data, bandwidth=None, percentile=None,
                         period=None, smoothing=None)
        self.result = self.get_max()

    def get_max(self):
        """
        Performs calculation of maximum value.

        Returns:
            maximums: Dictionary of maximum value for each channel.
        """
        maximums = {}
        times = {}
        if isinstance(self.reduction_data, (Stream, StationStream)):
            for trace in self.reduction_data:
                if trace.stats.standard.units == 'acc':
                    key = 'pga_time'
                elif trace.stats.standard.units == 'vel':
                    key = 'pgv_time'
                elif trace.stats.standard.units == 'disp':
                    key = 'pgd_time'
                else:
                    key = 'peak_time'
                idx = np.argmax(np.abs(trace.data))
                max_value = np.abs(trace.data[idx])
                max_time = trace.times(type='utcdatetime')[idx]
                maximums[trace.stats.channel] = max_value
                times[trace.stats.channel] = {key: max_time}
            return maximums, times
        else:
            for chan in self.reduction_data:
                maximums[chan] = np.abs(self.reduction_data[chan]).max()
            return maximums
