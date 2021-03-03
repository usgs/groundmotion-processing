# stdlib imports

# third party imports
import numpy as np
from numpy cimport ndarray
cimport numpy as np
cimport cython

cdef extern from "smoothing.h":
    void konno_ohmachi_c(double *spec, double *freqs, int np,
                         double *ko_freqs, double *ko_smooth, int nko,
                         double bandwidth);


def konno_ohmachi_smooth(np.ndarray[double, ndim=1, mode='c']spec,
                         np.ndarray[double, ndim=1, mode='c']freqs,
                         np.ndarray[double, ndim=1, mode='c']ko_freqs,
                         np.ndarray[double, ndim=1, mode='c']spec_smooth,
                         bandwidth):
    """
    """
    cdef int np = len(spec)
    cdef int nko = len(ko_freqs)

    konno_ohmachi_c(<double *>spec.data, <double *>freqs.data, np,
                    <double *>ko_freqs.data, <double *>spec_smooth.data,
                    nko, bandwidth)
    return
