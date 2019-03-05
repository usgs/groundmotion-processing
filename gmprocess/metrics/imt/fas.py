# third party imports
import numpy as np
from obspy.core.stream import Stream
from obspy.core.trace import Trace

# local imports
from gmprocess.metrics.exception import PGMException
from gmprocess.metrics.imc.geometric_mean import calculate_geometric_mean
from gmprocess.smoothing.konno_ohmachi import konno_ohmachi_smooth


def calculate_fas(stream, imcs, periods, smoothing, bandwidth):
    """
    Calculate the fourier amplitude spectra.

    This process requires getting the fourier amplitude spectra, applying
    the geometric mean to the horizontal traces, smoothing and returning the
    smoothed value for each requested period.

    Args:
        stream (obspy.core.stream.Stream): streams of strong ground motion.
            Traces in stream must be in units of g.
        imcs (list): list of imcs. (Currently only the geometric mean is
            supported and this is ignored. In the future it will account for
            channels and rotated channels.)

    Returns:
        dictionary: Dictionary of fas for the geometric mean.
            Units are in cm/s. The dictionary is structured as:
            fas_dict = {
                    <period> : <value,...
            }
    """
    fas_dict = {}
    sampling_rate = None
    # check units and add channel pga
    for trace in stream:
        if trace.stats['units'] != 'g' and trace.stats['units'] != 'cm/s/s':
            raise PGMException('Invalid units for sa: %r. '
                               'Units must be g (cm/s/s)' % trace.stats['units'])
        if 'Z' not in trace.stats['channel'].upper():
            sampling_rate = trace.stats.sampling_rate
    if sampling_rate is None:
        raise PGMException('No horizontal channels')

    spec_stream = Stream()
    for trace in stream:
        nfft = len(trace.data)
        # the fft scales so the factor of 1/nfft is applied
        spectra = abs(np.fft.rfft(trace.data, n=nfft)) / nfft
        spec_trace = Trace(data=spectra, header=trace.stats)
        spec_stream.append(spec_trace)

    ## The imc is always geometric mean. However, the combined stream is
    ## required rather than the single maximum value
    gm_trace = calculate_geometric_mean(spec_stream, return_combined=True)
    freqs = np.fft.rfftfreq(nfft, 1 / trace.stats.sampling_rate)

    fas_frequencies = 1 / np.asarray(periods)
    smoothed_values = np.empty_like(fas_frequencies)

    if smoothing.lower() == 'konno_ohmachi':
        konno_ohmachi_smooth(gm_trace.astype(np.double), freqs,
                fas_frequencies, smoothed_values, bandwidth)
    else:
        raise PGMException('Not a valid smoothing option: %r' % smoothing)

    for idx, freq in enumerate(fas_frequencies):
        fas_dict[1/freq] = smoothed_values[idx]

    return fas_dict
