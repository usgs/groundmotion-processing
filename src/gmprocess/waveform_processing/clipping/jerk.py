#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from gmprocess.waveform_processing.clipping.clip_detection import ClipDetection


class Jerk(ClipDetection):
    """
    Class for the jerk clipping detection algorithm.

    Attributes:
        st (StationStream):
            Record of three orthogonal traces.
        test_all (bool, default=False):
            If true, compute test values for all traces.
        is_clipped (bool):
            True if the record is clipped.
        point_thresh (float, default=25):
            Minimum number of flagged points required to label trace
            as clipped.
        num_outliers (int/list):
            The number of points with high jerk in the first clipped trace
            or list of number of points for each trace (if test_all=True).

    Methods:
        See parent class.
    """

    def __init__(self, st, point_thresh=400, test_all=False):
        """
        Constructs all neccessary attributes for the Max_Amp class.

        Args:
            st (StationStream):
                Record of three orthogonal traces.
            point_thresh (float, default=25):
                Minimum number of flagged points required to label trace
                as clipped.
            test_all (bool, default=False):
                If true, compute and store number of outliers for all traces.
        """
        ClipDetection.__init__(self, st.copy(), test_all)
        self.point_thresh = point_thresh
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
        Check for jerk outliers. Based on method described by:

            Ringler, A. T., L. S. Gee, B. Marshall, C. R. Hutt, and T. Storm
            (2012). Data Quality of Seismic Records from the Tohoku, Japan,
            Earthquake as Recorded across the Albuquerque Seismological
            Laboratory Networks, Seismol. Res. Lett. 83, 575–584.

        Args:
            tr (StationTrace):
                A single trace in the record.

        Returns:
            bool:
                Is the trace clipped?
        """
        temp_tr = tr.copy()
        # The algorithm was developed with time domain differentiation and so we want
        # to force this to be consistent regardless of config options.
        temp_tr.differentiate(frequency=False)
        temp_tr.differentiate(frequency=False)
        abs_diff = np.abs(temp_tr.data)
        median_x100 = 100 * np.median(abs_diff)
        (i_jerk,) = np.where(abs_diff >= median_x100)
        num_outliers = len(i_jerk)
        if self.test_all:
            self.num_outliers.append(num_outliers)
        else:
            self.num_outliers = num_outliers
        if num_outliers > self.point_thresh:
            return True
        return False

    def _get_results(self):
        """
        Iterates through and runs _detect() on each trace in the stream to
        determine if the record is clipped or not.

        See parent class.
        """
        return ClipDetection._get_results(self)
