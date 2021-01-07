# Phase Pickers

The `pickers` section of the config file controls options for estimating the
beginning of the signal window. The algorithm first estimates the P-wave
arrival time from a 1D velocity model using ObsPy's
[taup](https://docs.obspy.org/packages/obspy.taup.html#basic-usage) module. 

If the computed travel time arrives before the beginning of the record
start time, then the other methods are used to estimate the P-wave arrival.
We then select the method that results in the largest signal-to-noise ratio
among the alternative methods.

