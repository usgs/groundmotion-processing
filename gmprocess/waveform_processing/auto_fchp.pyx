import numpy as np
import obspy as obs
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
        if fabs(vx[i]) > output:
            output = fabs(vx[i])
    return output

@boundscheck(False)
@wraparound(False)
cdef complex[:] filtered_Facc(complex[:] Facc, double[:] freq, double fc, double order):
    cdef complex[:] filtered_Facc = np.zeros(len(freq), dtype="complex")
    cdef int u
    for u in range(len(freq)):
        if freq[u] == 0:
            filtered_Facc[u] = 0.0
        else:
            filtered_Facc[u] = Facc[u] / (sqrt(1.0 + pow(fc/freq[u], 2.0*order)))
    return filtered_Facc

@boundscheck(False)
@wraparound(False)
cdef double[:] get_vel(double[:] freq, complex[:] Facc):
    cdef complex[:] Fvel = np.zeros(len(freq), dtype="complex")
    cdef int u
    for u in range(len(freq)):
        if freq[u]==0:
            Fvel[u] = 0.0
        else:
            Fvel[u] = Facc[u]*9.81/(2.0j*M_PI*freq[u])
    return np.fft.irfft(Fvel)

@boundscheck(False)
@wraparound(False)
cdef double[:] get_disp(double[:] freq, complex[:] Facc):
    cdef complex[:] Fdisp = np.zeros(len(freq), dtype="complex")
    for u in range(len(freq)):
        if freq[u]==0:
            Fdisp[u] = 0.0
        else:
            Fdisp[u] = Facc[u]*9.81/(-4.0*M_PI*M_PI*freq[u]*freq[u])
    return np.fft.irfft(Fdisp)


@boundscheck(False)
@wraparound(False)
cdef double get_residual(double[:] time, double[:] disp, double target, int poly_order):
    cdef double [:] coef = np.polyfit(time[0:len(disp)], disp, poly_order)
    cdef double [:] disp_fit = np.zeros(len(disp))
    for i in range(len(disp)):
        disp_fit[i] = np.polyval(coef,time[i])
    return maxabs(disp_fit)/maxabs(disp) - target


def get_fchp(**kwargs):
    options = [
        "dt", "acc", "target", "tol", "poly_order", "maxiter", "fchp_min", 
        "fchp_max", "filter_order", "tukey_alpha", "filter_type"]
    
    for key, value in kwargs.items():
        if key not in options:
            print(f"{key} is not a valid argument. Please see documentation. Using "
                  "default values for all parameters that are not specified.")
    
    if "dt" in kwargs :
        dt = kwargs["dt"]
    else:
        print("You must specify dt")
        return
    
    if "acc" in kwargs:
        acc = np.asarray(kwargs["acc"], dtype="float64")
    else:
        print("You must specify acc")
        return
    
    if "target" in kwargs:
        target = kwargs["target"]
    else:
        target = 0.02
    
    if "tol" in kwargs:
        tol = kwargs["tol"]
    else:
        tol = 0.001
    
    if "poly_order" in kwargs:
        poly_order = kwargs["poly_order"]
    else:
        poly_order = 6
    
    if "maxiter" in kwargs:
        maxiter = kwargs["maxiter"]
    else:
        maxiter = 30
    
    if "fchp_min" in kwargs:
        minfc = kwargs["fchp_min"]
    else:
        minfc = 0.001
    
    if "fchp_max" in kwargs:
        maxfc = kwargs["fchp_max"]
    else:
        maxfc = 0.5
        
    if "filter_order" in kwargs:
        filter_order = kwargs["filter_order"]
    else:
        filter_order = 5.0
        
    if "tukey_alpha" in kwargs:
        tukey_alpha = kwargs["tukey_alpha"]
    else:
        tukey_alpha = 0.05
    
    if "filter_type" in kwargs:
        filter_type = kwargs["filter_type"]
    else:
        filter_type = 0
        
    # subtract mean and apply Tukey window
    cdef int i
    cdef double meanacc = 0.0
    for i in range(len(acc)):
        meanacc += acc[i]/len(acc)
    cdef double[:] window = signal.tukey(len(acc), alpha=tukey_alpha)
    for i in range(len(acc)):
        acc[i] = window[i] * (acc[i] - meanacc)
    cdef double[:] time = np.linspace(0, dt * len(acc), len(acc))
    cdef complex[:] Facc = np.fft.rfft(acc)
    cdef double[:] freq = np.fft.rfftfreq(len(acc), dt)
    
    cdef double fc0 = minfc
    cdef complex[:] FiltFacc = filtered_Facc(Facc, freq, fc0, filter_order)
    cdef double[:] disp = get_disp(freq, FiltFacc)
    cdef double R0 = get_residual(time, disp, target, poly_order)
    if(np.sign(R0) < 0):
        return fc0
    
    cdef double fc2 = maxfc
    if filter_type == 1:
        FiltFacc = filtered_Facc(Facc, freq, maxfc, filter_order)
    elif filter_type==0:
        tr = obs.Trace(acc, header={"dt":dt})
        tr.filter(
            type="highpass",
            freq=maxfc/(0.5/dt),
            corners=filter_order,
            zerophase=True,
        )
        FiltFacc = np.fft.rfft(tr.data)
    disp = get_disp(freq, FiltFacc)
    cdef double R2 = get_residual(time, disp, target, poly_order)
    if(np.sign(R2) > 0):
        return fc2
    
    cdef double fc1, R1, fc3, R3
    for i in range(maxiter):
        fc1 = np.exp(0.5 * (np.log(fc0) + np.log(fc2)))
        if filter_type==1:
            FiltFacc = filtered_Facc(Facc, freq, fc1, filter_order)
        elif filter_type==0:
            tr = obs.Trace(acc, header={"dt":dt})
            tr.filter(
                type="highpass",
                freq=fc1/(0.5/dt),
                corners=filter_order,
                zerophase=True,
            )
            FiltFacc = np.fft.rfft(tr.data)
        disp = get_disp(freq, FiltFacc)
        R1 = get_residual(time, disp, target, poly_order)
        fc3 = (np.exp(np.log(fc1) + (np.log(fc1) - np.log(fc0)) * np.sign(R0) * R1 / 
               (np.sqrt(R1*R1 - R0*R2))))
        if filter_type==1:
            FiltFacc = filtered_Facc(Facc, freq, fc3, filter_order)
        elif filter_type==0:
            tr = obs.Trace(acc, header={"dt":dt})
            tr.filter(
                type="highpass",
                freq=fc3/(0.5/dt),
                corners=filter_order,
                zerophase=True
            )
            FiltFacc = np.fft.rfft(tr.data)
        disp = get_disp(freq, FiltFacc)
        R3 = get_residual(time, disp, target, poly_order)
        if (np.abs(R3) <= tol) or (i == maxiter - 1):
            return fc3
        if R1 * R3 < 0:
            fc0 = fc1
            fc2 = fc3
            R0 = R1
            R2 = R3
        elif np.sign(R2) != np.sign(R3):
            fc0 = fc2
            fc2 = fc3
            R0 = R2
            R2 = R3
        else:
            fc0 = fc0
            fc2 = fc3
            R0 = R0
            R2 = R3