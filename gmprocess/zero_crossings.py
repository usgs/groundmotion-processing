import numpy as np


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
        zarray = np.multiply(tr.data[0:-2], tr.data[1:-1])
        zindices = [i for (i, z) in enumerate(zarray) if z < 0]
        zero_count_tr = len(zindices)

        z_rate = zero_count_tr/dur

        tr.setParameter('ZeroCrossingRate',
                        {'crossing_rate': z_rate})

        # Fail if zero crossing rate is too low
        if z_rate <= min_crossings:
            tr.fail('Zero crossing rate too low.')

    return st
