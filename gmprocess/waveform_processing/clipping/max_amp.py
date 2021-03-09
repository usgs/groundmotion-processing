import numpy as np
from ClipDetection import ClipDetection


class Max_amp(ClipDetection):
    '''
    A class to represent the Maximum Amplitude method for clipping detection

    Attributes:
        MAX_AMP (int):
            A threshold for the absolute maximum amplitude of the trace.
        st (StationStream):
            Stream of data.
        classifications (list):
            List of bools indicating if clipped/unclipped (1,0) for each trace.

    Methods:
        _detect():
            Determines if the trace is clipped or not.
        get_results():
            Iterates through each trace in each stream of stream_collection
            to run _detect on.
    '''
    def __init__(self, st, MAX_AMP=6e6):
        '''
        Constructs all neccessary attributes for the Std Dev method object

        Args:
            st (StationStream):
                Stream of data.
            MAX_AMP (int):
                A threshold for the absolute maximum amplitude of the trace.
        '''
        ClipDetection.__init__(self, st.copy(), MAX_AMP=MAX_AMP)

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
        If any point exceeds the threshold, fail the trace.
        Threshold is given as MAX_AMP, the absolute maximum amplitude of
        the trace.

        Args:
            clip_tr (StationTrace):
                Trace of data.

        Returns:
            bool:
                Did the trace passed the test?
        '''
        tr_abs = np.abs(clip_tr.copy())
        if tr_abs.max() > self.MAX_AMP:
            return True
        return False

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