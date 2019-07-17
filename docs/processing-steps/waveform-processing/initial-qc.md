# Initial Quality Control

There are numerous quality control steps that can be applied to the data
to screen out problematic records. Most of these rely on successfully
identifying the signal window, and having sufficient duration in the
pre-event noise window.

If a data source does not provide signficant pre-event data to estimate
the noise, one can turn off these automated checks and manually review
the records.

When a record does not pass a quality control check, then it will be
marked as "failed" and the reason for the failure will be recorded.
This information will be reviewable in the processing report that is
generated at the end, or through inspection of the output data.


## `check_free_field`

The file readers to their best to determine whether or not a station is
placed in a free field location or not. If the `reject_non_free_field`
option is set to True, then non free field stations will be marked as
"failed."


## `check_max_amplitude`

This is a very simple way to screen out clipped records, and is only
applicable for non-strong-motion instruments. Priort to applying the
instrument response and converting to physical units, the maximum count
value is checked, and the record is marked as "failed" if the specified
`max` value is exceed.

We have also encountered problematic data where the count never exceeds
a reasonable minimum. So we also check that the maximum count exceeds
the specified `min` value.

## `max_traces`

Reliably handling instrumental arrays is not possible in our automated
code, largely because the location code is not used in a systematic
manner. Thus, this check marks any instrument that has more than `n_max`
channels as "failed".

## `min_sample_rate`

For many applications, a minimum sample rate may be required. While this
is slightly redundant with the instrumental codes that can be set
querying the data, this is an extra check to ensure a minimum sample
rate.

## `check_zero_crossings`

This option allows you to require a minimum number of zero crossings per
second within the signal window. This is intended to screen out instrumental
failures, in particular instrumental resets, but can sometimes result
in incorrectly screening out good records.

## `check_sta_lta`

This check the STA-to-LTA ratio (STA is "short term average" and LTA is
"long term average"). The ratio is computed for record the full recond
and the max value must exceed the selected threshold. The units are
seconds for window lenghts.

Importantly, this is one of the only QA checks that does not rely on
correct windowing of the singal and noise, so it can be applied for
records for which no pre-event noise is available. However, we have
found that it often results in the rejection of data that would
otherwise be considered acceptable.

## `compute_snr`

This processing step checks the signa-to-noise ratio (SNR), requiring that
the minimum SNR exceeds the selected `threshold` between `min_freq` and
`max_freq` where the Fourier spectra of the signal and noise are smoothed
using the Konno-Omachi method with the selected `bandwidth` parameter.
