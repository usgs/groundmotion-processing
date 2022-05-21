## Pickers

This section is to configure how the P-wave arrival is estimated. We have found
that for the purposes of splitting the signal and noise windows, the estimated
P-wave arrival time based on the event origin time and a simple 1D velocity
model is more reliable than most of the alternatives that were available at
the time. 

The primary concern in this context is to avoid an estimate that is too late, 
which would inlucde some of the signal energy into the noise window. This would 
cause otherwise acceptable records to be rejected. A P-wave estimate that is 
too early would only have the downside of shortening the noise window 
slightly. This motivated the `p_arrival_shift` option. This allows you to 
artificially shift the P-wave by a constsant to avoid the more problematic 
late arriving estimate errors.

The reason that this section also includes alternative pickers that do not 
rely on travel time is because some ground motion data does not have reliable
start times of the record. In these cases, travel time estimates fail and so 
we fall back on the alternatives. In this case, the esimate that results in 
the best signal-to-noise ratio is used.

Note that the alternative picker algorithms require lots of options and we have
stuck with the default values. We include the values here to provide flexibility
to the user but refer the user to the documentation of each method (e.g., in
ObsPy) for additional information.

```yaml
pickers:
    p_arrival_shift: -1.0

    # Options for obspy.signal.trigger.ar_pick()
    ar:
        # Frequency of the lower bandpass window (Hz)
        f1: 1.0

        # Frequency of the upper bandpass window (Hz)
        f2: 20.0

        # Length of LTA for the P arrival (seconds)
        lta_p: 1.0

        # Length of STA for the P arrival (seconds)
        sta_p: 0.1

        # Length of LTA for the S arrival (seconds)
        lta_s: 4.0

        # Length of STA for the S arrival (seconds)
        sta_s: 1.0

        # Number of AR coefficients for the P arrival
        m_p: 2

        # Number of AR coefficients for the S arrival
        m_s: 8

        # Length of variance window for the P arrival (seconds)
        l_p: 0.1

        # Length of variance window for the S arrival (seconds)
        l_s: 0.2

        # If True, also pick the S phase. Otherwise only the P phase.
        s_pick: False

```

% Indices and tables

% ==================

% * :ref:`genindex`

% * :ref:`modindex`

% * :ref:`search`
