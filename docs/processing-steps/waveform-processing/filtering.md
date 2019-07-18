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

## lowpass_max_frequency

The lowpass corner frequency should not exceed the Nyquist frequency.
This processing step allows you to set a factor `fn_fac` that is
multiplied by the record's Nyquist frequency, which is then used as
a cap on the lowpass corner frequency.

## adjust_highpass_corner

The highpass corner frequency can be adjusted such that the displacement
series does not result in unreasonable values. These steps are based on the
algorithm described by
Dawood et al. ([2016](https://doi.org/10.1193/071214EQS106)).

This algorithm begins with an initial corner frequency that was selected
as configured in the `get_corner_frequencies` step. It then checks the
criteria descibed below; if the criteria are not met then the high pass
corner is increased with the multiplicative step factor (`step_factor`)
until the criteria are met, or the corner frequency exceeds
`maximum_freq`.

Acceptance criteria:

* The final displacement of the record does not exceed
  `max_final_displacement` (in cm).

* The ratio of the final displacement to the maximum displacement to the
  maximum displacement does not exceed `max_displacment_ratio`
  

## highpass_filter

Applies a Butterworth highpass filter using the highpass corner determined
from prior steps that modify the highpass corner frequency. Options include
`filter_order` and `number_of_passes`.

## lowpass_filter

Applies a Butterworth lowpass filter using the lowpass corner determined
from prior steps that modify the lowpass corner frequency. Options include
`filter_order` and `number_of_passes`.


