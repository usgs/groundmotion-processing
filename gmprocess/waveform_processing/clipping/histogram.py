#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from gmprocess.waveform_processing.clipping.clip_detection import ClipDetection


class Histogram(ClipDetection):
    """
    Class for the standard deviation clipping detection algorithm.

    Attributes:
        st (StationStream):
            Record of three orthogonal traces.
        test_all (bool, default=False):
            If true, compute and store number of clipped intervals for
            all traces.
        is_clipped (bool):
            True if the record is clipped.
        num_bins (int, default=6200):
            Number of bins for amplitude histogram.
        min_width (int, default=7):
            Minimum width of a bump to be indicative of clipping.
        search_width_bins (int, default=700):
            Bin grouping size.
        num_clip_intervals(int/list):
            The number of clipped intervals in the first clipped trace
            or list of number of points for each trace (if test_all=True).

    Methods:
        See parent class.
    """

    def __init__(
        self, st, num_bins=6200, min_width=7, search_width_bins=700, test_all=False
    ):
        """
        Constructs all neccessary attributes for the Histogram class.

        Args:
            st (StationStream):
                Stream of data.
            test_all (bool, default=False):
                If true, compute and store number of clipped intervals for
                all traces.
            num_bins (int, default=6200):
                Number of bins for amplitude histogram.
            min_width (int, default=7):
                Minimum width of a bump to be indicative of clipping.
            search_width_bins (int, default=700):
                Bin grouping size.
        """
        ClipDetection.__init__(self, st.copy(), test_all)
        self.num_bins = num_bins
        self.min_width = min_width
        self.search_width_bins = search_width_bins
        if self.test_all:
            self.num_clip_intervals = []
        else:
            self.num_clip_intervals = None
        self._get_results()

    def _signal_scale(self, signal, alpha):
        """
        Helper function to scale signal data

        Args:
            signal (StationTrace.data):
                Data to be scaled
            alpha (float):
                Scale factor

        Returns:
            The scaled signal data
        """
        new_signal = signal * alpha
        return new_signal

    def _find_peaks(self, signal, thresh, should_sort):
        """
        Helper function to find peaks in signal data

        Args:
            signal (StationTrace.data):
                Data to be scaled
            thresh (float):
                Data threshold value
            should_sort (bool):
                Should the peaks list be sorted

        Returns:
            peaks (list):
                List of determined peaks in the data
        """
        peaks = []
        for idx in range(1, len(signal) - 1):
            cur_x = signal[idx]
            if cur_x >= thresh:
                prev_x = signal[idx - 1]
                next_x = signal[idx + 1]
                if (cur_x > prev_x) and (cur_x > next_x):
                    peaks.append((cur_x, idx))
        # Sort descending
        if should_sort:
            peaks.sort(key=lambda tup: tup[0])
        return peaks

    def _merge_intervals(self, clip_intervals, max_distance_apart):
        """
        Helper function to merge clipping intervals

        Args:
            clip_intervals (list):
                List of tuples corresponding to start and end of peaks
            max_distance_apart (int):
                Maximum distance between intervals

        Returns:
            merged_intervals (list):
                List of merged clipping intervals corresponding to the peaks
        """
        num_intervals = len(clip_intervals)
        if num_intervals == 0:
            return []
        # Sorting the intervals places candidates for merging in adjacent\
        # slots in the array.
        sorted_intervals = list(self._sort_intervals_by_start(clip_intervals))
        merged_intervals = []
        # This loop calculates the distance between each pair of
        # candidate intervals, and merges them if the distance is smaller
        # than |max_distance_apart|.
        merged_intervals.append(sorted_intervals[0])
        num_merged_intervals = 1
        for interval_idx in range(0, num_intervals - 1):
            left_interval = merged_intervals[num_merged_intervals - 1]
            right_interval = sorted_intervals[interval_idx + 1]
            # Check to merge.
            distance_apart = right_interval[0] - left_interval[1]
            if distance_apart <= max_distance_apart:
                new_start = left_interval[0]
                # This handles the case when one interval is entirely within
                # a bigger interval.
                new_stop = max(left_interval[1], right_interval[1])
                # new_interval = (new_start, new_stop)
                # We need to replace the most recent interval with the newly
                # merged interval, or there will be duplicates.
                merged_intervals[num_merged_intervals - 1] = (new_start, new_stop)
            else:
                # We don't merge, so we can just append the right interval.
                merged_intervals.append(right_interval)
                num_merged_intervals += 1
        return merged_intervals

    def _sort_intervals_by_start(self, clip_intervals):
        """
        Helper function to sort clipping intervals by starting index

        Args:
            clip_intervals (list):
                List of tuples corresponding to start and end of peaks

        Returns:
             clip_intervals (list):
                List of sorted tuples corresponding to start and end of peaks.
        """
        clip_intervals.sort(key=lambda tup: tup[0])
        return clip_intervals

    def _get_clip_intervals(self, signal, peaks, thresh):
        """
        Helper function to obtain clipping intervals

        Args:
            signal (StationTrace.data):
                Data signal suspected to feature clipping
            peaks (list):
                List of critical data points
            thresh (float):
                Threshold for difference between a point and the average of
                points around it.

        Returns:
             clip_intervals (list):
                List of sorted tuples corresponding to where signal is clipped
        """
        clip_intervals = []
        for _, cur_peak_loc in peaks:
            # Descend left.
            working_avg = abs(signal[cur_peak_loc])
            start_idx = cur_peak_loc
            left_idx = cur_peak_loc - 1
            num_iters = 1
            while left_idx >= 1:
                num_iters = num_iters + 1
                cur_mag = abs(signal[left_idx])
                prev_mag = abs(signal[left_idx + 1])
                working_avg = (((num_iters - 1) * working_avg) / num_iters) + (
                    cur_mag / num_iters
                )
                avg_diff = abs(working_avg - cur_mag)
                if avg_diff > thresh:
                    start_idx = left_idx + 1
                    break
                # We hit a sample outside of the clipping range. Save the
                # sample to the right, because it's the last sample in the
                # clipping range.
                cur_derivative = abs(cur_mag - prev_mag)
                if cur_derivative > thresh:
                    start_idx = left_idx + 1
                    break
                left_idx = left_idx - 1
            # Decend right.
            working_avg = abs(signal[cur_peak_loc])
            stop_idx = cur_peak_loc
            right_idx = cur_peak_loc + 1
            num_iters = 1
            while right_idx < len(signal):
                num_iters = num_iters + 1
                cur_mag = abs(signal[right_idx])
                prev_mag = abs(signal[right_idx - 1])
                working_avg = (((num_iters - 1) * working_avg) / num_iters) + (
                    cur_mag / num_iters
                )
                avg_diff = abs(working_avg - cur_mag)
                if avg_diff > thresh:
                    stop_idx = right_idx - 1
                    break
                # We hit a sample outside of the clipping range. Save the
                # sample to the right, because it's the last sample in the
                # clipping range.
                cur_derivative = abs(cur_mag - prev_mag)
                if cur_derivative > thresh:
                    stop_idx = right_idx - 1
                    break
                right_idx = right_idx + 1
            if start_idx != stop_idx:
                clip_intervals.append((start_idx, stop_idx))
        clip_intervals = self._merge_intervals(clip_intervals, 1)
        return clip_intervals

    def _clean_trace(self, tr):
        """
        Pre-processing steps.

        Args:
            tr (StationTrace):
                A single trace in the record.

        Returns:
            clean_tr (StationTrace):
                Cleaned trace.
        """
        t_1 = tr.stats.starttime
        t_2 = t_1 + 180
        clean_tr = tr.copy()
        clean_tr.trim(t_1, t_2)
        return clean_tr

    def _detect(self, tr):
        """
        Test for clipping using the histogram-based method. This is a slight
        variation on the method described by:

            Laguna, C. and Lerch, A. (2016). September. An efficient algorithm
            for clipping detection and declipping audio. In Audio Engineering
            Society Convention 141. Audio Engineering Society.

        Args:
            tr (StationTrace):
                A single trace in the record.

        Returns:
            bool:
                Is the trace clipped?
        """
        init_method = "estimated"
        amp_hist, edges = np.histogram(tr.data, bins=self.num_bins)
        temp_forward_1 = ExponentialSmoothing(
            amp_hist.astype(float), initialization_method=init_method
        )
        forward_1 = temp_forward_1.fit(smoothing_level=0.2).fittedvalues
        temp_amp_hist = ExponentialSmoothing(
            forward_1[::-1].astype(float), initialization_method=init_method
        )
        amp_hist = temp_amp_hist.fit(smoothing_level=0.2).fittedvalues[::-1]
        temp_forward_2 = ExponentialSmoothing(
            amp_hist.astype(float), initialization_method=init_method
        )
        forward_2 = temp_forward_2.fit(smoothing_level=0.025).fittedvalues
        temp_smoothed_amp_hist = ExponentialSmoothing(
            forward_2[::-1].astype(float), initialization_method=init_method
        )
        smoothed_amp_hist = temp_smoothed_amp_hist.fit(
            smoothing_level=0.025
        ).fittedvalues[::-1]
        novelty = amp_hist - smoothed_amp_hist
        negative_clip_lower_idx = -1
        negative_clip_upper_idx = -1
        in_bump = False
        width = 0
        for idx in range(0, self.search_width_bins):
            cur_val = novelty[idx]
            # In a bump
            if cur_val > 1:
                if in_bump:
                    width += 1
                else:
                    width = 1
                    in_bump = True
            # Outside of bump
            else:
                if in_bump:
                    # The clipping threshold has been found
                    if width > self.min_width:
                        negative_clip_lower_idx = idx
                        negative_clip_upper_idx = negative_clip_lower_idx - width
                        break
                    width = 0
                    in_bump = False
        nov_len = len(novelty)
        positive_clip_lower_idx = -1
        positive_clip_upper_idx = -1
        in_bump = False
        width = 0
        for idx in range(len(novelty) - 1, nov_len - self.search_width_bins - 1, -1):
            cur_val = novelty[idx]
            # In a bump
            if cur_val > 1:
                if in_bump:
                    width += 1
                else:
                    width = 1
                    in_bump = True
            # Outside of bump
            else:
                if in_bump:
                    # The clipping threshold has been found
                    if width > self.min_width:
                        positive_clip_lower_idx = idx
                        positive_clip_upper_idx = idx + width
                        break
                    width = 0
                    in_bump = False
        has_negative_clip = False
        negative_thresh = -100
        negative_width = -1
        if negative_clip_lower_idx > 0:
            has_negative_clip = True
            # We should use the lower edge for the clipping threshold and the
            # upper edge for the width.
            negative_thresh = edges[negative_clip_lower_idx + 1]
            negative_upper = edges[negative_clip_upper_idx]
            negative_width = (negative_thresh - negative_upper) / 2
        has_positive_clip = False
        positive_thresh = 100
        positive_width = -1
        if positive_clip_lower_idx > 0:
            has_positive_clip = True
            # We should use the lower edge for the clipping threshold and
            # the upper edge for the width.
            positive_thresh = edges[positive_clip_lower_idx]
            positive_upper = edges[positive_clip_upper_idx + 1]
            positive_width = (positive_upper - positive_thresh) / 2
        # Now to find the clipping intervals based on the clipping levels.
        negative_clip_intervals = []
        if has_negative_clip:
            invert_x = self._signal_scale(tr.data, -1)
            valleys = self._find_peaks(invert_x, abs(negative_thresh), True)
            negative_clip_intervals = self._get_clip_intervals(
                tr.data, valleys, negative_width
            )
        positive_clip_intervals = []
        if has_positive_clip:
            peaks = self._find_peaks(tr.data, positive_thresh, True)
            positive_clip_intervals = self._get_clip_intervals(
                tr.data, peaks, positive_width
            )
        # Aggregate the positive and negative clipping intervals.
        clip_intervals = negative_clip_intervals + positive_clip_intervals
        clip_intervals = self._merge_intervals(clip_intervals, 1)
        num_clip_intervals = len(clip_intervals)
        if self.test_all:
            self.num_clip_intervals.append(num_clip_intervals)
        else:
            self.num_clip_intervals = num_clip_intervals
        if num_clip_intervals > 0:
            return True
        return False

    def _get_results(self):
        """
        Iterates through and runs _detect() on each trace in the stream to
        determine if the record is clipped or not.

        See parent class.
        """
        return ClipDetection._get_results(self)
