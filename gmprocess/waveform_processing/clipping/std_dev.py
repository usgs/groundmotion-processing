import numpy as np
from ClipDetection import ClipDetection


class Std_dev(ClipDetection):
    '''
    A class to represent the Std Dev method for clipping detection

    Attributes:
        AMP_THRESH (float):
            Threshold for maximum/minimum amplitude of trace.
        N_STD (int):
            Number of neigboring points to calculate std dev with.
        STD_THRESH (float):
            Maximum threshold for std dev.
        st (StationStream):
                Stream of data.

    Methods:
        _detect(tr):
            Determines if the trace is clipped or not.
        get_results():
            Iterates through each trace in each stream of stream_collection to
            run _detect on.
    '''
    def __init__(self, st, AMP_THRESH=0.85, N_STD=12, STD_THRESH=0.001):
        '''
        Constructs all neccessary attributes for the Std Dev method object

        Args:
            st_collection (list):
                List of stream collection objects.
            AMP_THRESH (float, default = 0.85):
                Threshold for maximum/minimum amplitude of trace.
            N_STD (int, default = 12):
                Number of neigboring points to calculate std dev with.
            STD_THRESH (float, default = 0.001):
                Maximum threshold for std dev.
        '''
        ClipDetection.__init__(self, st, AMP_THRESH=AMP_THRESH,
                               N_STD=N_STD, STD_THRESH=STD_THRESH)

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
        For all points with amplitude greater than AMP_THRESH, calculate
        standard deviation (std) of N_STD neighboring points. Fail the trace
        if the std of N_STD neighboring points is less than STD_THRESH for
        any N points.

        Args:
            clip_tr (StationTrace):
                Trace of data.
        Returns:
            bool:
                Did the trace passed the test?
        '''
        low_std = False
        tr_std = clip_tr.copy()
        tr_std.data = np.zeros(len(clip_tr.data))
        thresh_max = self.AMP_THRESH * np.max(clip_tr.data)
        thresh_min = self.AMP_THRESH * np.min(clip_tr.data)
        for i in range(len(clip_tr.data) - self.N_STD):
            tr_std.data[i] = np.std(clip_tr.data[i:i + self.N_STD])
        i_lowstd, = np.where((tr_std.data < self.STD_THRESH) &
                             ((clip_tr.data >= thresh_max) |
                             (clip_tr.data <= thresh_min)))
        if len(i_lowstd) > 5:
            low_std = True
        return low_std

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