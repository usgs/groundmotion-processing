## Processing

In order for the processing steps to be fully modular, this section is a
list of dictionaries rather than a single dictionary. Each dictionary 
represents a processing step, in which the single key of the dictionary is
the name of the processing step, and the value is a dictionary of arguments
for that processing step function.

```{tip}
Each step dictionary (e.g., `- detrend`) can be edited, removed, added, 
and duplicated. This allows for users to customize the processing for
different needs and preferences. 
```

Some example processing steps are given below. The full list set of examples 
can be found in the config file in the repository 
[here](https://github.com/usgs/groundmotion-processing/blob/master/gmprocess/data/config_production.yml).

```yaml
processing:
    # Check number of traces for each instrument. Max is useful for screening
    # out downhole or structural arrays with the same station code.
    - check_instrument:
        n_max: 3
        n_min: 2
        require_two_horiz: True

    - detrend:
        # Supported obspy methods:
        #     constant, demean, linear, polynomial, simple, spline
        # Also:
        #     baseline_sixth_order, pre
        detrending_method: linear

    - get_corner_frequencies:
        # Corner frequency selection can use constant values, or selected
        # dynamically from the signal-to-noise-ratio.

        # Valid options for "method" are "constant" and "snr".
        method: snr

        constant:
            highpass: 0.08
            lowpass: 20.0

        snr:
            # For dynamic filtering, we require a minimum SNR threshold between
            # as configured in the snr_check step.
            same_horiz: True
```



% Indices and tables

% ==================

% * :ref:`genindex`

% * :ref:`modindex`

% * :ref:`search`
