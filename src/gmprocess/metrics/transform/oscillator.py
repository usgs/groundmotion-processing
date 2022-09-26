#!/usr/bin/env python
# -*- coding: utf-8 -*-

from obspy.core.trace import Trace

# Local import
from gmprocess.core.stationtrace import StationTrace
from gmprocess.core.stationstream import StationStream
from esi_core.gmprocess.metrics.oscillators import calculate_spectrals
from gmprocess.metrics.transform.transform import Transform
from gmprocess.utils.constants import GAL_TO_PCTG


class oscillator(Transform):
    """Class for computing the oscillator for a given period."""

    def __init__(
        self,
        transform_data,
        damping,
        period,
        times,
        max_period,
        allow_nans,
        bandwidth,
        config,
    ):
        """
        Args:
            transform_data (StationStream):
                Intensity measurement component.
            damping (float):
                Damping for spectral amplitude calculations.
            period (float):
                Period for spectral amplitude calculations.
            times (numpy.ndarray):
                Times for the spectral amplitude calculations.
            allow_nans (bool):
                Should nans be allowed in the smoothed spectra. If False, then
                the number of points in the FFT will be computed to ensure
                that nans will not result in the smoothed spectra.
            config (dict):
                Configuration options.

        """
        super().__init__(
            transform_data,
            damping=damping,
            period=period,
            times=times,
            max_period=max_period,
            allow_nans=allow_nans,
            bandwidth=bandwidth,
            config=config,
        )
        self.period = period
        self.damping = damping
        self.times = times
        self.result = self.get_oscillator(config)

    def get_oscillator(self, config=None):
        """
        Calculated the oscillator of each trace's data.

        Args:
            config (dict):
                Configuration options.

        Returns:
            spectrals: StationStream or numpy.ndarray with the oscillator data.
        """
        spectrals = get_spectral(
            self.period,
            self.transform_data,
            damping=self.damping,
            times=self.times,
            config=config,
        )
        return spectrals


def get_spectral(period, stream, damping=0.05, times=None, config=None):
    """
    Returns a stream of spectral response with units of %%g.

    Args:
        period (float):
            Period for spectral response.
        stream (StationStream):
            Strong motion timeseries for one station.
        damping (float):
            Damping of oscillator.
        times (np.ndarray):
            Array of times for the horizontal channels. Default is None.
        config (dict):
            StationStream.

    Returns:
        StationStream.
    """

    # Use as-recorded or upsampled record?
    use_upsampled = False
    dt = stream[0].stats.delta
    ns = (int)(10.0 * dt / period - 0.01) + 1
    if ns > 1:
        use_upsampled = True
        dt = stream[0].getCached("upsampled")["dt"]

    if "rotated" in stream.getStreamParamKeys():
        # For ROTD and GMROTD
        rotated = []
        if use_upsampled:
            rotated_data = stream.getStreamParam("upsampled_rotated")
        else:
            rotated_data = stream.getStreamParam("rotated")

        for idx in range(len(rotated_data)):
            rot_matrix = rotated_data[idx]
            rotated_spectrals = []
            # This is the loop over rotation angles
            for idy in range(0, len(rot_matrix)):
                stats = {
                    "npts": len(rot_matrix[idy]),
                    "delta": dt,
                    "sampling_rate": 1.0 / dt,
                }
                new_trace = Trace(data=rot_matrix[idy], header=stats)
                sa_list = new_and_improved_calculate_spectrals(
                    new_trace, period, damping
                )
                acc_sa = sa_list[0]
                acc_sa *= GAL_TO_PCTG
                rotated_spectrals.append(acc_sa)
            rotated += [rotated_spectrals]

        # Add rotated data to stream parameters
        stream.setStreamParam("rotated_oscillator", rotated)
        return stream
    else:
        traces = []
        # For anything but ROTD and GMROTD
        for idx in range(len(stream)):
            trace = stream[idx]
            if use_upsampled:
                trace_dict = stream[idx].getCached("upsampled")
                stats = {
                    "npts": trace_dict["np"],
                    "delta": dt,
                    "sampling_rate": 1.0 / dt,
                }
                temp_trace = Trace(data=trace_dict["data"], header=stats)
            else:
                temp_trace = trace
            sa_list = new_and_improved_calculate_spectrals(temp_trace, period, damping)
            acc_sa = sa_list[0]
            acc_sa *= GAL_TO_PCTG
            stats = trace.stats.copy()
            stats.npts = sa_list[3]
            stats.delta = sa_list[4]
            stats.sampling_rate = sa_list[5]
            stats["units"] = "%%g"
            spect_trace = StationTrace(data=acc_sa, header=stats, config=config)
            traces += [spect_trace]
        spect_stream = StationStream(traces)
        return spect_stream


def new_and_improved_calculate_spectrals(trace, period, damping):
    """
    Pull some stuff out of cython that shouldn't be there.
    """
    new_dt = trace.stats.delta
    new_np = trace.stats.npts
    new_sample_rate = trace.stats.sampling_rate
    tlen = (new_np - 1) * new_dt
    # This is the resample factor for low-sample-rate/high-frequency
    ns = (int)(10.0 * new_dt / period - 0.01) + 1
    if ns > 1:
        # Increase the number of samples as necessary
        new_np = new_np * ns
        # Make the new number of samples a power of two
        # leaving this out for now; it slows things down but doesn't
        # appear to affect the results. YMMV.
        # new_np = 1 if new_np == 0 else 2**(new_np - 1).bit_length()
        # The new sample interval
        new_dt = tlen / (new_np - 1)
        # The new sample rate
        new_sample_rate = 1.0 / new_dt
        # Make a copy because resampling happens in place
        trace = trace.copy()
        # Resample the trace
        trace.resample(new_sample_rate, window=None)

    sa_list = calculate_spectrals(
        trace.data, new_np, new_dt, new_sample_rate, period, damping
    )
    return sa_list
