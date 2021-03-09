import numpy as np
from ClipDetection import ClipDetection
from statsmodels.tsa.holtwinters import ExponentialSmoothing


class Histogram(ClipDetection):
    '''
    A class to represent the Histogram method for clipping detection

    Attributes:
        NUM_BINS (int):
            Number of bins for amplitude histogram.
        MIN_WIDTH (int):
            Minimum width of a bump to be indicative of clipping.
        SEARCH_WIDTH_BINS (int):
            Bin grouping size.
        st (StationStream):
            Stream of data.

    Methods:
        _detect(tr):
            Determines if the trace is clipped or not.
        get_results():
            Iterates through each trace in each stream of stream_collection
            to run _detect on.
    '''
    def __init__(self, st, NUM_BINS=6200, MIN_WIDTH=7,
                 SEARCH_WIDTH_BINS=700):
        '''
        Constructs all neccessary attributes for the Histogram method object

        Args:
            st (StationStream):
                Stream of data.
            NUM_BINS (int, default = 6300):
                Number of bins for amplitude histogram.
            MIN_WIDTH (int, default = 7):
                Minimum width of a bump to be indicative of clipping.
            SEARCH_WIDTH_BINS (int, default = 700):
                Bin grouping size
        '''
        ClipDetection.__init__(self, st,
                               NUM_BINS=NUM_BINS, MIN_WIDTH=MIN_WIDTH,
                               SEARCH_WIDTH_BINS=SEARCH_WIDTH_BINS)

    def _clean_trace(self, clip_tr):
        '''
        Helper function to clean the trace

        Args:
            clip_tr (StationTrace):
                Trace of data.

        Returns:
            clip_tr (StationTrace):
                Cleaned trace of data.
        '''
        return ClipDetection._clean_trace(self, clip_tr)

    def _signal_scale(self, signal, alpha):
        '''
        Helper function to scale signal data

        Args:
            signal (StationTrace.data):
                Data to be scaled
            alpha (float):
                Scale factor

        Returns:
            The scaled signal data
        '''
        new_signal = signal * alpha
        return new_signal

    def _find_peaks(self, signal, thresh, should_sort):
        '''
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
        '''
        peaks = []
        for idx in range(1, len(signal) - 1):
            cur_x = signal[idx]
            if cur_x >= thresh:
                prev_x = signal[idx-1]
                next_x = signal[idx+1]
                if (cur_x > prev_x) and (cur_x > next_x):
                    peaks.append((cur_x, idx))
        # Sort descending
        if should_sort:
            # Look at this sorting here
            peaks.sort(key=lambda tup: tup[0])
        return peaks

    def _merge_intervals(self, clip_intervals, max_distance_apart):
        '''
        Helper function to merge clipping intervals

        Args:
            clip_intervals (list):
                List of tuples corresponding to start and end of peaks
            max_distance_apart (int):
                Maximum distance between intervals

        Returns:
            merged_intervals (list):
                List of merged clipping intervals corresponding to the peaks
        '''
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
                merged_intervals[num_merged_intervals - 1] = (new_start,
                                                              new_stop)
            else:
                # We don't merge, so we can just append the right interval.
                merged_intervals.append(right_interval)
                num_merged_intervals += 1
        return merged_intervals

    def _sort_intervals_by_start(self, clip_intervals):
        '''
        Helper function to sort clipping intervals by starting index

        Args:
            clip_intervals (list):
                List of tuples corresponding to start and end of peaks

        Returns:
             clip_intervals (list):
                List of sorted tuples corresponding to start and end of peaks.
        '''
        clip_intervals.sort(key=lambda tup: tup[0])
        return clip_intervals

    def _get_clip_intervals(self, signal, peaks, thresh):
        '''
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
        '''
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
                working_avg = (((num_iters - 1) * working_avg) / 
                              num_iters) + \
                              (cur_mag / num_iters)
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
                working_avg = (((num_iters - 1) * working_avg) /
                              num_iters) + \
                              (cur_mag / num_iters)
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

    def _detect(self, clip_tr):
        '''
        Test for clipping using the histogram-based method. This is a slight
        variation on the method described by:

            Laguna, C. and Lerch, A. (2016). September. An efficient algorithm
            for clipping detection and declipping audio. In Audio Engineering
            Society Convention 141. Audio Engineering Society.

        Args:
            clip_tr (StationTrace):
                Trace of data.

        Returns:
            bool:
                Did the trace passed the test?
        '''
        amp_hist, edges = np.histogram(clip_tr.data, bins=self.NUM_BINS)
        temp_forward_1 = ExponentialSmoothing(amp_hist.astype(np.float))
        forward_1 = temp_forward_1.fit(smoothing_level=0.2).fittedvalues
        temp_amp_hist = ExponentialSmoothing(forward_1[::-1].astype(np.float))
        amp_hist = temp_amp_hist.fit(smoothing_level=0.2).fittedvalues[::-1]
        temp_forward_2 = ExponentialSmoothing(amp_hist.astype(np.float))
        forward_2 = temp_forward_2.fit(smoothing_level=0.025).fittedvalues
        temp_smoothed_amp_hist = ExponentialSmoothing(forward_2[::-1].astype(np.float))
        smoothed_amp_hist = temp_smoothed_amp_hist.fit(smoothing_level=0.025).fittedvalues[::-1]
        novelty = amp_hist - smoothed_amp_hist
        negative_clip_lower_idx = -1
        negative_clip_upper_idx = -1
        in_bump = False
        width = 0
        for idx in range(0, self.SEARCH_WIDTH_BINS):
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
                    if width > self.MIN_WIDTH:
                        negative_clip_lower_idx = idx
                        negative_clip_upper_idx = negative_clip_lower_idx - \
                                                  width
                        break
                    width = 0
                    in_bump = False
        nov_len = len(novelty)
        positive_clip_lower_idx = -1
        positive_clip_upper_idx = -1
        in_bump = False
        width = 0
        for idx in range(len(novelty)-1, nov_len - self.SEARCH_WIDTH_BINS - 1, -1):
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
                    if width > self.MIN_WIDTH:
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
            invert_x = self._signal_scale(clip_tr.data, -1)
            valleys = self._find_peaks(invert_x, abs(negative_thresh), True)
            negative_clip_intervals = self._get_clip_intervals(clip_tr.data,
                                                               valleys,
                                                               negative_width)
        positive_clip_intervals = []
        if has_positive_clip:
            peaks = self._find_peaks(clip_tr.data, positive_thresh, True)
            positive_clip_intervals = self._get_clip_intervals(clip_tr.data,
                                                               peaks,
                                                               positive_width)
        # Aggregate the positive and negative clipping intervals.
        clip_intervals = negative_clip_intervals + positive_clip_intervals
        clip_intervals = self._merge_intervals(clip_intervals, 1)
        if clip_intervals:
            return True
        return False

    def get_results(self):
        '''
        Iterate through each stream collection in stream_collection,
        each stream in the stream collection, and then through each trace
        in the stream to run on _detect method.

        Args:
            None

        Returns:
            list (bools):
                Which traces passed the test and were marked as
                clipped/unclipped.
        '''
        return ClipDetection.get_results(self)