import numpy as np
import logging


def check_zero_crossings(st, min_crossings=1.0):
    """
    Check for a large enough density.

    This is intended to screen out instrumental failures or resetting.
    Value determined empirically from observations on the GeoNet network
    by R Lee.

    Args:
        st (StationStream):
            StationStream object.
        min_crossings (float):
            Minimum average number of zero crossings per second for the
            full trace.
    """

    zero_count_tr = []
    delta_t = st[0].stats.delta
    dur = (st[0].stats.npts - 1) * delta_t

    for tr in st:
        # Make a copy of the trace to trim it before counting crossings; we do
        # not want to modify the trace but we only want to count the crossings
        # within the trimmed window
        trcopy = tr.copy()

        if tr.hasParameter('signal_end'):
            etime = tr.getParameter('signal_end')['end_time']
            split_time = tr.getParameter('signal_split')['split_time']

            trcopy.trim(starttime=split_time, endtime=etime)

        zarray = np.multiply(trcopy.data[0:-1], trcopy.data[1:])
        zindices = [i for (i, z) in enumerate(zarray) if z < 0]
        zero_count_tr = len(zindices)

        z_rate = zero_count_tr / dur

        # Put results back into the original trace, not the copy
        tr.setParameter('ZeroCrossingRate',
                        {'crossing_rate': z_rate})

        # Fail if zero crossing rate is too low
        if z_rate <= min_crossings:
            tr.fail('Zero crossing rate too low.')

    return st
