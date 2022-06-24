## Metrics

This section is for configuring how ground motion metrics are calculated. 

The first two sections control the intensity measure types (IMTs) and intensity
measure components (IMCs) that will be computed.

```yaml
metrics:
  # Output IMCs
  # Valid IMCs: channels, geometric_mean, gmrotd,
  # greater_of_two_horizontals, rotd
  output_imcs: [ROTD50, channels]
  # Output IMTs
  # Valid IMTs: arias, fas, pga, pgv, sa, duration, sorted_duration
  output_imts: [PGA, PGV, SA, duration, sorted_duration]
```
Some of the metrics require additional specifications and so they have separate
dedicated dictionaries.

```yaml
  sa:
      # damping used to calculate the spectral response
      damping: 0.05
      # periods for which the spectral response is calculated
      periods:
        # Parameters defining an array of periods
        # syntax is the same as that used for numpy linspace and logspace
        # start (first value), stop (last value), num (number of values)
        start: 1.0
        stop: 3.0
        num: 3
        # Valid spacing: linspace, logspace
        spacing: linspace
        # Defines whether the above array is used. If False, only the
        # defined_periods are used
        use_array: False
        # Defines a list of user defined periods that are not
        # predefined by the array of periods
        defined_periods: [0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25,
          0.3, 0.4, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 7.5, 10.0]
  fas:
      smoothing: konno_ohmachi
      bandwidth: 20.0
      allow_nans: True
      periods:
        # Parameters defining an array of periods
        # syntax is the same as that used for numpy linspace and logspace
        # start (first value), stop (last value), num (number of values)
        start: 1.0
        stop: 3.0
        num: 3
        # Valid spacing: linspace, logspace
        spacing: linspace
        # Defines whether the above array is used. If false, only the
        # defined_periods are used
        use_array: True
        # A list of user defined periods that are not
        # predefined by the array of periods.
        defined_periods: [0.3]
  duration:
      intervals: [5-75, 5-95]
```

Lastly, there is an optional section to specify a map of Vs30 which will be
used estimate Vs30 for each station. This may contain several keys. Each key
must be unique, and must have four attributes: 
  - `file` -- Path to the grid file that can be loaded using MapIO.
  - `column_header` -- The column header used in the flatfile.
  - `readme_entry` -- The description used in the README file.
  - `units` -- Units that will be stored in the StationMetrics XML.

```yaml
  vs30:
      example_key:
        file: example_file
        column_header: example_column_header
        readme_entry: example_readme_entry
        units: example_units
```


% Indices and tables

% ==================

% * :ref:`genindex`

% * :ref:`modindex`

% * :ref:`search`
