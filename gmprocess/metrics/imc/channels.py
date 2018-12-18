# third party imports
import numpy as np


def calculate_channels(stream, **kwargs):
    """Return the pgm for each channel in a given input Stream.

    NB: The input Stream should have already been "processed",
    i.e., filtered, detrended, tapered, etc.)

    Args:
        stream (Obspy Stream): Stream containing one or Traces of
            acceleration data in gals.
        kwargs (**args): Ignored by this class.

    Returns:
        dictionary: Dictionary of peak ground motion for each channel.
    """
    channels_dict = {}
    for trace in stream:
        channel = trace.stats['channel']
        channels_dict[channel] = np.abs(trace.max())
    return channels_dict
