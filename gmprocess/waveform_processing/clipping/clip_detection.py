#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Module for individual/heuristic clipping methods. These get combined
with the neurual network model (clipping_ann.py). The NN model gets
called by clipping_check.py module.
"""


class ClipDetection:
    """
    Parent class for clipping detection algorithms.

    Attributes:
        st (StationStream):
            Record of three orthogonal traces.
        test_all (bool, default=False):
            If true, compute test values for all traces.
        is_clipped (bool):
            True if the record is clipped.

    Methods:
        _detect():
            Determines if the trace is clipped or not.
        _clean_trace():
            Trim and normalize a trace.
        _get_results():
            Iterates through and runs _detect() on each trace in the stream.
    """

    def __init__(self, st, test_all=False):
        """
        Constructs all neccessary attributes for the ClipDetection method
        object.

        Args:
            st (StationStream):
                Stream of data.
            test_all (bool, default=False):
                If true, compute test values for all traces.
        """
        self.st = st.copy()
        self.is_clipped = False
        self.test_all = test_all

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
        return tr

    def _detect(self, clip_tr):
        """
        Clipping detection algorithm for the individual child class

        Args:
            tr (StationTrace):
                A single trace in the record.

        Returns:
            bool:
                Did the trace pass the test?
        """
        pass

    def _get_results(self):
        """
        Iterates through and runs _detect() on each trace in the stream to
        determine if the record is clipped or not.

        Args:
            None

        Returns:
            None
        """
        for tr in self.st:
            tr = self._clean_trace(tr)
            temp_is_clipped = self._detect(tr)
            if temp_is_clipped:
                self.is_clipped = temp_is_clipped
                if self.test_all:
                    continue
                else:
                    break
