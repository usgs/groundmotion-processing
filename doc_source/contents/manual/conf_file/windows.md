## Signal and Noise Windows

Separating the signal and noise windows is an important step in *gmprocess*. 
This is based on an estimate of the P-wave arrival time, and the options for
estimating the P-wave arrival are set in the {ref}`Pickers` section. The options
in this section control how the end of the signal window is estimated relative
to the P-wave time and minimum window duration requirements. 

The end of the signal can be set using an assumed phase velocity. 
Alternatively, it can be set with duration model, where the mean 5-95%
significant duration (Ds) is added to the split time. The mean Ds can also
be extended by a number of standard deviations (epsilon).


```yaml
windows:
    signal_end:
        # Valid options for "method" are "velocity" and "model"
        method: model
        vmin: 1.0
        # Minimum duration in sec for use with 'vmin' option.
        floor: 120.0
        # Duration model
        model: AS16
        # Number of standard deviations; if epsilon is 1.0, then the signal
        # window duration is the mean Ds + 1 standard deviation.
        epsilon: 3.0

    window_checks:
        # Minimum noise duration; can be zero but this will allow for errors
        # to occur if requesting signal-to-noise ratios.
        do_check: True
        min_noise_duration: 1.0
        min_signal_duration: 5.0
```


% Indices and tables

% ==================

% * :ref:`genindex`

% * :ref:`modindex`

% * :ref:`search`
