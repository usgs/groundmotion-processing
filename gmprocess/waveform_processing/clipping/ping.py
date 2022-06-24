#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from gmprocess.waveform_processing.clipping.clip_detection import ClipDetection


class Ping(ClipDetection):
    """
    Class for the ping clipping detection algorithm.

    Attributes:
        st (StationStream):
            Record of three orthogonal traces.
        test_all (bool, default=False):
            If true, compute and store number of outlying points for
            all traces.
        is_clipped (bool):
            True if the record is clipped.
        percent_thresh (float, default=0.57):
            Percent of data range serving as a multiplicative factor
            to determine ping threshold.
        num_outliers (int/list):
            The number of points with difference exceeding threshold
            in the first clipped trace or list of number of points for
            each trace (if test_all=True).

    Methods:
       See parent class.
    """

    def __init__(self, st, percent_thresh=0.57, test_all=False):
        """
        Constructs all neccessary attributes for the Ping class.

        Args:
            st (StationStream):
                Record of three orthogonal traces.
            percent_thresh (float, default=0.57):
                Percent of data range serving as a multiplicative factor
                to determine ping threshold.
            test_all (bool, default=False):
                If true, compute and store number of outlying points for
                all traces.
        """
        ClipDetection.__init__(self, st.copy(), test_all)
        self.percent_thresh = percent_thresh
        if self.test_all:
            self.num_outliers = []
        else:
            self.num_outliers = None
        self._get_results()

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
        If any two points differ by more than a threshold, fail the trace.
        Threshold given as percent_thresh * datarange.

        Args:
            tr (StationTrace):
                A single trace in the record.

        Returns:
            bool:
                Is the trace clipped?
        """
        data_range = np.abs(np.max(tr.data)) - np.min(tr.data)
        tr_diff = np.abs(np.diff(tr))
        points_outlying = [val > self.percent_thresh * data_range for val in tr_diff]
        num_outliers = np.count_nonzero(points_outlying)
        if self.test_all:
            self.num_outliers.append(num_outliers)
        else:
            self.num_outliers = num_outliers
        if num_outliers > 0:
            return True
        return False

    def _get_results(self):
        """
        Iterates through and runs _detect() on each trace in the stream to
        determine if the record is clipped or not.

        See parent class.
        """
        return ClipDetection._get_results(self)
