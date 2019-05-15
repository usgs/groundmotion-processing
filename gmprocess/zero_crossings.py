import numpy as np


def check_zero_crossings(st, min_crossings=10):
    """
    Check for a large enough density.

    This is intended to screen out instrumental failures or resetting.
    Value determined empirically from observations on the GeoNet network
    by R Lee.
    """

    zero_count_tr = []
    delta_t = st[0].stats.delta
    t = np.arange(len(st[0].data))*delta_t

    for tr in st:
        zarray = np.multiply(tr.data[0:-2], tr.data[1:-1])
        zindices = [i for (i, z) in enumerate(zarray) if z < 0]
        zero_count_tr = len(zindices)

        z_rate = 10*zero_count_tr/t[-1]

        tr.setParameter('ZeroCrossingRate',
                        {'crossing_rate': z_rate})

        if zero_count_tr <= min_crossings:
            tr.fail('Zero crossing rate too low.')

    return st
