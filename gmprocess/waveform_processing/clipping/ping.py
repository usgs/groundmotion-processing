import numpy as np
from ClipDetection import ClipDetection


class Ping(ClipDetection):
    '''
    A class to represent the ping method for clipping detection

    Attributes:
        PERCENTAGE (float):
            Multiplicative factor to determine ping threshold.
        st (StationStream):
                Stream of data.

    Methods:
        _detect():
            Determines if the trace is clipped or not.
        get_results():
            Iterates through each trace in each stream of stream_collection to
            run _detect on.
    '''
    def __init__(self, st, PERCENTAGE=0.55):
        '''
        Constructs all neccessary attributes for the Ping method object

        Args:
            st (StationStream):
                Stream of data.
            PERCENTAGE (float, default = 0.55):
                Multiplicative factor to determine ping threshold.
        '''
        ClipDetection.__init__(self, st, PERCENTAGE=PERCENTAGE)

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

    def _detect(self, clip_tr):
        '''
        If any two points differ by more than a threshold, fail the trace.
        Threshold is given as PERCENTAGE * datarange.

        Args:
            clip_tr (StationTrace):
                Trace of data.

        Returns:
            bool:
                Did the trace passed the test?
        '''
        is_ping = False
        data_range = np.abs(np.max(clip_tr.data)) - np.min(clip_tr.data)
        tr_diff = np.abs(np.diff(clip_tr))
        if any(tr_diff > self.PERCENTAGE*data_range):
            is_ping = True
        return is_ping

    def get_results(self):
        '''
        Iterate through each stream collection in stream_collection, each
        stream in the stream collection, and then through each trace in
        the stream to run on _detect method.

        Args:
            None

        Returns:
            list (bools):
                Which traces passed the test and were marked as
                clipped/unclipped.
        '''
        return ClipDetection.get_results(self)