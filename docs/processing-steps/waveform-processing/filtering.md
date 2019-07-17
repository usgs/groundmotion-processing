# Filtering

Filtering is broken down into a series of processing steps.


## get_corner_frequencies

The first step is to select the highpass and lowpass corner frequencies, as
configured in the `get_corner_frequencies` step. There are two suppored
methods: `constant` and `snr`. Each method has additional parameters that
are set via their respective subsections. 


The `snr` method requires an accurate estimate of the signal-to-noise, which
is not always possible. This is why we provide the `constant` method, where
the highpass and lowpass corners are manually selected and constant for all
records.

The `snr` method selects the highpass and lowpass corner frequencies such
that the SNR criteria specified in the `compute_snr` section are satisfied
for the resulting passband. In other words, the SNR for the frequencies in
the passband are guaranteed to exceed the `threshold` specified under
`compute_snr/check/threshold`. The corner frequencies are determined
independently for each channel if `same_horiz` is set to False; otherwise
the horizontal channels are forced to have the same corner frequencies,
where the high of the highpass corners and the lower of the lowpass corners
of the two channels are selected. 
