# Third party imports
import numpy as np
from scipy import integrate

# Local imports
from gmprocess.constants import GAL_TO_PCTG
from gmprocess.metrics.reduction.reduction import Reduction
from gmprocess.stationstream import StationStream
from gmprocess.stationtrace import StationTrace


class Arias(Reduction):
    """Class for calculation of arias intensity."""
    def __init__(self, reduction_data, bandwidth=None, percentile=None,
            period=None, smoothing=None):
        """
        Args:
            reduction_data (obspy.core.stream.Stream or numpy.ndarray): Intensity
                    measurement component.
            percentile (float): Percentile for rotation calculations. Default
                is None.
            period (float): Period for smoothing (Fourier amplitude spectra)
                    calculations. Default is None.
            smoothing (string): Smoothing type. Default is None.
            bandwidth (float): Bandwidth for the smoothing operation. Default
                    is None.
        """
        super().__init__(reduction_data, bandwidth=None, percentile=None,
                period=None, smoothing=None)
        self.arias_stream = None
        self.result = self.get_arias()


    def get_arias(self):
        """
        Performs calculation of arias intensity.

        Returns:
            arias_intensities: Dictionary of arias intensity for each channel.
        """
        arias_intensities = {}
        arias_stream = StationStream([])
        for trace in self.reduction_data:
            dt = trace.stats['delta']
            # convert from cm/s/s to m/s/s
            acc = trace.data * 0.01

            # Calculate Arias Intensity
            integrated_acc2 = integrate.cumtrapz(acc * acc, dx=dt)
            arias_intensity = integrated_acc2 * np.pi * GAL_TO_PCTG / 2
            channel = trace.stats.channel
            trace.stats.standard.units = 'veloc'
            trace.stats.npts = len(arias_intensity)
            arias_stream.append(StationTrace(arias_intensity, trace.stats))
            arias_intensities[channel] = np.abs(np.max(arias_intensity))
        self.arias_stream = arias_stream
        return arias_intensities
