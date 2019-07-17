class Reduction(object):
    """Base class for reduction calculations."""
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
        self.reduction_data = reduction_data
