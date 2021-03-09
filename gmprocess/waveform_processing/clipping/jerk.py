import numpy as np
from ClipDetection import ClipDetection


class Jerk(ClipDetection):
    '''
    A class to represent the jerk method for clipping detection

    Attributes:
        POINT_THRESH (float):
            Minimum number of flagged points required to label trace
            as clipped.
        st (StationStream):
                Stream of data.

    Methods:
        _detect(tr):
            Determines if the trace is clipped or not.
        get_results():
            Iterates through each trace in each stream of stream_collection to
            run _detect on.
    '''
    def __init__(self, st, POINT_THRESH=25):
        '''
        Constructs all neccessary attributes for the Jerk method object

        Args:
            st (StationStream):
                Stream of data.
            POINT_THRESH (float, default = 25):
                Minimum number of flagged points required to label trace
                as clipped.
        '''
        ClipDetection.__init__(self, st, POINT_THRESH=POINT_THRESH)

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
        Check for jerk outliers. Based on method described by:

            Ringler, A. T., L. S. Gee, B. Marshall, C. R. Hutt, and T. Storm
            (2012). Data Quality of Seismic Records from the Tohoku, Japan,
            Earthquake as Recorded across the Albuquerque Seismological
            Laboratory Networks, Seismol. Res. Lett. 83, 575–584.

        Args:
            clip_tr (StationTrace):
                Trace of data.

        Returns:
            bool:
                Did the trace passed the test?
        '''
        temp_st = self.st.copy()
        temp_st.differentiate()
        if clip_tr.stats.channel[1] == 'H':
            temp_st.differentiate()
        abs_diff = np.abs(clip_tr.data)
        median_x100 = 100*np.median(abs_diff)
        i_jerk, = np.where(abs_diff >= median_x100)
        if len(i_jerk) > self.POINT_THRESH:
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