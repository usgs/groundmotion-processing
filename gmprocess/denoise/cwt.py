# -*- coding: utf-8 -*-

#
# ======================================================================
#
#                           Gabriel Ferragut
#              U.S. Geological Survey/ University of Oregon
#                       
#
#           Modified from Chuck Langston's BC_Seis MATLAB program
# ======================================================================
#


# def cwt_fw(x, type, nv, dt):
    
#     return
    

# def cwt_iw(Wx, type, nv):

#     ## Need to get the size of the Wavelet signal. In MATLAB, this is a matrix ... Here probably use two arrays.
    
#     # Get the length of the input time series for octave/voice calculation
#     n = len(Wx)
    
#     # Padding the signal (optionally)
#         # What exactly is big N in Chuck's code?
        
#     N = 2**(1 + round(log2(n)))
    
#     n1 = (N-n)/2     #Possibly apply Python version of matlab floor() function here
#     n2 = n1
    
#     if (2*n1+n) % 2 == 1:
#         n2 = n1 + 1
    
    
#     return