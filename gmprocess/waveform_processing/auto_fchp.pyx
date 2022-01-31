# This is code for adjusting the high-pass corner developed by Scott Brandenberg
# at UCLA. This is experimental code.

import numpy as np
cimport numpy as np
cimport cython
from cython cimport boundscheck, wraparound
from libc.math cimport fabs, sqrt, pow, M_PI
from scipy import signal

@boundscheck(False)
@wraparound(False)
cdef double maxabs(double[:] vx):
    cdef int i
    cdef int N = vx.shape[0]
    cdef double output = 0.0
    for i in range(N):
        if(fabs(vx[i])>output):
            output = fabs(vx[i])
    return output

@boundscheck(False)
@wraparound(False)
cdef complex[:] filtered_Facc(complex[:] Facc, double[:] freq, double fc, double order):
    cdef complex[:] filtered_Facc = np.zeros(len(freq), dtype='complex')
    cdef int u
    for u in range(len(freq)):
        if (freq[u] == 0):
            filtered_Facc[u] = 0.0
        else:
            filtered_Facc[u] = Facc[u] / (sqrt(1.0 + pow(fc/freq[u], 2.0*order)))
    return filtered_Facc

@boundscheck(False)
@wraparound(False)
cdef double[:] get_vel(double[:] freq, complex[:] Facc):
    cdef complex[:] Fvel = np.zeros(len(freq), dtype='complex')
    cdef int u
    for u in range(len(freq)):
        if(freq[u]==0):
            Fvel[u] = 0.0
        else:
            Fvel[u] = Facc[u]*9.81/(2.0j*M_PI*freq[u])
    return np.fft.irfft(Fvel)

@boundscheck(False)
@wraparound(False)
cdef double[:] get_disp(double[:] freq, complex[:] Facc):
    cdef complex[:] Fdisp = np.zeros(len(freq), dtype='complex')
    for u in range(len(freq)):
        if(freq[u]==0):
            Fdisp[u] = 0.0
        else:
            Fdisp[u] = Facc[u]*9.81/(-4.0*M_PI*M_PI*freq[u]*freq[u])
    return np.fft.irfft(Fdisp)


@boundscheck(False)
@wraparound(False)
cdef double get_residual(double[:] time, double[:] disp, double target):
    cdef double [:] coef = np.polyfit(time[0:len(disp)], disp, 6)
    cdef double [:] dcoef = np.asarray([6.0*coef[0], 5.0*coef[1], 4.0*coef[2], 3.0*coef[3], 2.0*coef[4], 1.0*coef[5]], dtype='double')
    cdef double maxdisp = maxabs(disp)
    cdef double maxfit = np.max([np.abs(np.polyval(coef, np.min(time))), np.abs(np.polyval(coef, np.max(time)))])
    cdef complex [:] root_vals = np.roots(dcoef).astype('complex')
    cdef int i
    for i in range(len(root_vals)):
        if(np.imag(root_vals[i])!=0):
            continue
        else:
            if((np.real(root_vals[i])>np.min(time)) and (np.real(root_vals[i])<np.max(time))):
                if(np.polyval(coef, np.real(root_vals[i])) > maxfit):
                    maxfit = np.polyval(coef, np.real(root_vals[i]))
    return maxfit/maxdisp - target


def get_fchp(double dt, double[:] acc, double target, double tol, double order, int maxiter, double minfc, double maxfc):
    # subtract mean and apply Tukey window
    cdef int i
    cdef double meanacc=0.0
    for i in range(len(acc)):
        meanacc += acc[i]/len(acc)
    cdef double[:] window = signal.tukey(len(acc), alpha=0.2)
    for i in range(len(acc)):
        acc[i] = window[i] * (acc[i] - meanacc)
    cdef double[:] time = np.linspace(0, dt * len(acc), len(acc))
    cdef complex[:] Facc = np.fft.rfft(acc)
    cdef double[:] freq = np.fft.rfftfreq(len(acc), dt)
    
    cdef double fc0 = minfc
    cdef complex[:] FiltFacc = filtered_Facc(Facc, freq, fc0, order)
    cdef double[:] disp = get_disp(freq, FiltFacc)
    cdef double R0 = get_residual(time, disp, target)
    if(np.sign(R0) < 0):
        return fc0
    
    cdef double fc2 = maxfc
    FiltFacc = filtered_Facc(Facc, freq, maxfc, order)
    disp = get_disp(freq, FiltFacc)
    cdef double R2 = get_residual(time, disp, target)
    if(np.sign(R2) > 0):
        return fc2
    
    cdef double fc1, R1, fc3, R3
    for i in range(maxiter):
        fc1 = np.exp(0.5 * (np.log(fc0) + np.log(fc2)))
        FiltFacc = filtered_Facc(Facc, freq, fc1, order)
        disp = get_disp(freq, FiltFacc)
        R1 = get_residual(time, disp, target)
        fc3 = np.exp(np.log(fc1) + (np.log(fc1) - np.log(fc0)) * np.sign(R0) * R1 / (np.sqrt(R1*R1 - R0*R2)))
        FiltFacc = filtered_Facc(Facc, freq, fc3, order)
        disp = get_disp(freq, FiltFacc)
        R3 = get_residual(time, disp, target)
        if ((np.abs(R3) <= tol) or (i == maxiter - 1)):
            return fc3
        if (R1 * R3 < 0):
            fc0 = fc1
            fc2 = fc3
            R0 = R1
            R2 = R3
        elif (np.sign(R2) != np.sign(R3)):
            fc0 = fc2
            fc2 = fc3
            R0 = R2
            R2 = R3
        else:
            fc0 = fc0
            fc2 = fc3
            R0 = R0
            R2 = R3