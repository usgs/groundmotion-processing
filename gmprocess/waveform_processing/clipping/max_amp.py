#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from gmprocess.waveform_processing.clipping.clip_detection import ClipDetection


class Max_Amp(ClipDetection):
    """
    Class for the maximum amplitude clipping detection algorithm.

    Attributes:
        st (StationStream):
            Record of three orthogonal traces.
        test_all (bool, default=False):
            If true, compute and store max amp for all traces.
        is_clipped (bool):
            True if the record is clipped.
        max_amp_thresh (float, default=6e6):
            A threshold for the absolute maximum amplitude of the trace.
        max_amp (float/list):
            The maximum amplitude of the first clipped trace or list of
            max amps for each trace (if test_all=True).

    Methods:
        See parent class.
    """

    def __init__(self, st, max_amp_thresh=6e6, test_all=False):
        """
        Constructs all neccessary attributes for the Max_Amp method.

        Args:
            st (StationStream):
                Record of three orthogonal traces.
            max_amp_thresh (float, default=6e6):
                A threshold for the absolute maximum amplitude of the trace.
            test_all (bool, default=False):
                If true, compute and store max amp for all traces.
        """
        ClipDetection.__init__(self, st.copy(), test_all)
        self.max_amp_thresh = max_amp_thresh
        if self.test_all:
            self.max_amp = []
        else:
            self.max_amp = None
        self._get_results()

    def _clean_trace(self, tr):
        """
        Helper function to clean a trace (no normalizing in this
        algorithm).

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
        clean_tr.detrend(type="constant")
        return clean_tr

    def _detect(self, tr):
        """
        If any point exceeds the threshold, fail the trace. Threshold is
        given as max_amp_thresh, the absolute maximum amplitude of
        the trace.

        Args:
            tr (StationTrace):
                A single trace in the record.

        Returns:
            bool:
                Is the trace clipped?
        """
        tr_abs = np.abs(tr.copy())
        abs_max_amp = tr_abs.max()
        if self.test_all:
            self.max_amp.append(abs_max_amp)
        else:
            self.max_amp = abs_max_amp
        if abs_max_amp > self.max_amp_thresh:
            return True
        return False

    def _get_results(self):
        """
        Iterates through and runs _detect() on each trace in the stream to
        determine if the record is clipped or not.

        See parent class.
        """
        return ClipDetection._get_results(self)
