# Third party imports
import numpy as np
from scipy import integrate

# Local imports
from gmprocess.utils.constants import GAL_TO_PCTG
from gmprocess.metrics.reduction.reduction import Reduction

# Hard code percentiles for duration now. Need to make this conigurable.
P_START = 0.05
P_END = 0.95


class Duration(Reduction):
    """Class for calculation of duration."""

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
        self.result = self.get_duration()

    def get_duration(self):
        """
        Performs calculation of arias intensity.

        Returns:
            durations: Dictionary of arias intensity for each channel.
        """
        durations = {}
        for trace in self.reduction_data:
            dt = trace.stats['delta']
            # convert from cm/s/s to m/s/s
            acc = trace.data * 0.01
            time = trace.times()

            # Calculate Arias Intensity
            integrated_acc2 = integrate.cumtrapz(acc * acc, dx=dt)
            arias_intensity = integrated_acc2 * np.pi * GAL_TO_PCTG / 2

            # Normalized AI
            ai_norm = arias_intensity / np.max(arias_intensity)

            ind0 = np.argmin(np.abs(ai_norm - P_START))
            ind1 = np.argmin(np.abs(ai_norm - P_END))

            dur595 = time[ind1] - time[ind0]
            channel = trace.stats.channel
            durations[channel] = np.abs(np.max(dur595))

        return durations
