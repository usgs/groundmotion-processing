class ClipDetection():
    '''
    A parent class for clipping detection methods.

    Attributes:
        Method-specific hyperparamters:
            See individual method files
        stream_collection (list):
            List of stream collection objects.
        classifications (list):
            List of bools indicating if clipped/unclipped (1,0) for each trace.

    Methods:
        _detect(tr):
            Determines if the trace is clipped or not.
        get_results():
            Iterates through each trace in each stream of stream_collection
            to run _detect on.
    '''
    def __init__(self, st, PERCENTAGE=0.55, POINT_THRESH=25,
                 STD_THRESH=0.001, AMP_THRESH=0.85, N_STD=12,
                 MAX_AMP=6e6, NUM_BINS=1000, MIN_WIDTH=2,
                 SEARCH_WIDTH_BINS=700):
        '''
        Constructs all neccessary attributes for the ClipDetection method
        object.

        Args:
            st (StationStream):
                Stream of data.
            Method-specific hyperparamters:
                See individual method files.
        '''
        self.st = st.copy()
        self.is_clipped = False
        self.PERCENTAGE = PERCENTAGE
        self.POINT_THRESH = POINT_THRESH
        self.STD_THRESH = STD_THRESH
        self.AMP_THRESH = AMP_THRESH
        self.N_STD = N_STD
        self.MAX_AMP = MAX_AMP
        self.NUM_BINS = NUM_BINS
        self.MIN_WIDTH = MIN_WIDTH
        self.SEARCH_WIDTH_BINS = SEARCH_WIDTH_BINS

    def _clean_trace(self, clip_tr):
        '''
        Helper function to clean the trace

        Args:
            tr (StationTrace):
                Trace of data.

        Returns:
            tr (StationTrace):
                Cleaned trace of data.
        '''
        t_1 = clip_tr.stats.starttime
        t_2 = t_1 + 180
        clip_tr.trim(t_1, t_2)
        clip_tr.detrend(type='constant')
        if not bool(self.MAX_AMP):
            clip_tr.normalize()
        return clip_tr

    def _detect(self, clip_tr):
        '''
        Clipping detection algorithm for the individual child class

        Args:
            clip_tr (StationTrace):
                Trace of data.

        Returns:
            bool:
                Did the trace pass the test?
        '''
        pass

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
                clipped/unclipped
        '''
        for clip_tr in self.st:
            clip_tr = self._clean_trace(clip_tr)
            self.is_clipped = self._detect(clip_tr)
            if self.is_clipped:
                break
        return self.is_clipped