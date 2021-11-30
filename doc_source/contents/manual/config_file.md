# Configuration File

The config file is the primary means by which users can adjust and customize
*gmprocess*. While the config file includes comments to help explain the values
and their units, the config file in the repository 
[here](https://github.com/usgs/groundmotion-processing/blob/master/gmprocess/data/config_production.yml)
is also a useful reference because sections or comments can be removed from the
config file for a given project. Also, the config file in the repository should
stay updated when the code changes. An outdated config file is a common source 
of confusion when updating *gmprocess* because updating the code does not update
the config file that is installed for existing projects and so the config will
get out of date.

The following sections correspond to the top-level sections of the config file.


## User Information

This is one of the shorter sections and simply includes user information. This
information used to populate the SEIS-PROV documents. While this may seem like
a minor issue, know the creator of a dataset is very important. 

Example:

```yaml
user:
  name: Test user
  email: test@email.com
```


## Data Fetchers

This section includes subsections corresponding to the data fetchers that will
be used by the `download` subcommand. While each fetcher is optional, at least
one fetcher is required to run the `download` subcommand. Individual fetchers
can be "turned off" by deleting or commenting them out of the config file.

Note that some of the fetchers require the user to fill in information for
authentication purposes (e.g., an email address for the CESMD fetcher).

The CESMD fetcher is given as an example below. The full list set of examples
can be found in the config file in the repository 
[here](https://github.com/usgs/groundmotion-processing/blob/master/gmprocess/data/config_production.yml).

```yaml
fetchers:
    CESMDFetcher:
        # CESMD requires an email, register yours by
        # visiting this page:
        # https://strongmotioncenter.org/cgi-bin/CESMD/register.pl
        email: EMAIL
        process_type: raw
        station_type: Ground
        # define the distance search radius (km)
        eq_radius: 10.0
        # define the time search threshokd (sec)
        eq_dt: 10.0
        # station search radius (km)
        station_radius: 100.0
```


## Reader Optoins

This is a short section with some reader-specific options. 

```yaml
read:
    # Look for StationXML files in this directory instead of the `<event>/raw`
    # directory. StationXML file names must follow the convension of 
    # `<network>.<station>.xml`.
    metadata_directory: None

    # Resampling rate if times are unevenly spaced
    resample_rate: 200.0

    # SAC header doesn't include units (!) and is generally assumed to be:
    #     nm/s/s for acceleration
    #     nm/s   for velocity
    #     nm     for displacement
    # The following is a multiplicative factor to convert the SAC data to
    # cm/s/s for accel or cm/s for velocity.
    sac_conversion_factor: 1e-7      # For nm/s/s
    # sac_conversion_factor: 1e-4    # For um/s/s
    # sac_conversion_factor: 980.665 # For g

    # Also, data source is not included in SAC headers, so we provide an option
    # to set it here:
    sac_source: Unknown
```


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


## Processing

In order for the processing steps to be fully modular, this section is a
list of dictionaries rather than a single dictionary. Each dictionary 
represents a processing step, in which the single key of the dictionary is
the name of the processing step, and the value is a dictionary of arguments
for that processing step function.

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


## Colocated Instruments

This section is for handling colocated instruments that have otherwise passed
tests. The `preference` argument is a list of channel codes in order of
preference. 

```yaml
colocated:
    preference: ["HN?", "BN?", "HH?", "BH?"]
```

## Handling Duplicates

This section is for handling duplicate data when creating a StreamCollection.
Stations are classified as duplicates in a somewhat complex manner. The reason
for this is that a more straight forward approach based solely on network, 
station, and channel codes is not possible because some data formats do not 
provide network codes. Thus, we determine whether two StationTraces are 
duplicates by checking the station, channel codes, and the distance between 
them.

```yaml
    # Maximum distance tolerance (in m) for duplicate data
    max_dist_tolerance: 500.0

    # List of preferences (in order) for handling duplicate data.
    preference_order: ['process_level', 'source_format', 'starttime', 'npts',
                       'sampling_rate', 'location_code']

    # Preference for selecting process level when faced with duplicate data
    # but with different processing levels. Must be a list containing
    # 'V0', 'V1', and 'V2'. The first item is the most preferred,
    # and the last item is the least preferred.
    process_level_preference: ['V1', 'V0', 'V2']

    # Preference for selecting the format when faced with duplicate data
    # but with different source formats. Must be a list containing the source
    # format abbreviations found in gmprocess.io. Does not need to contain
    # all possible formats.

    # Example to always prefer COSMOS files over DMG files
    format_preference: ['cosmos', 'dmg']
```

## Summary Report

This is for building a report, with a one-page summary of the data in each
StationStream per page. It will write out the latex file, and then look for
the `pdflatex` command and attempt to build the pdf. This requires the 
`summary_plots` function to have been run previously.

Currently, this section is really just a place holder and has to be exactly as
given below. We anticipate adding new options that would be set here. 

```yaml
build_report:
    format: latex
```

## Metrics

This section is for configuring how ground motion metrics are calculated. 

The first two sections control the intensity measure types (IMTs) and intensity
measure components (IMCs) that will be computed.

```yaml
metrics:
  # Output IMCs
  # Valid IMCs: channels, geometric_mean, gmrotd,
  # greater_of_two_horizontals, rotd
  output_imcs:
      - ROTD50
      - channels
  # Output IMTs
  # Valid IMTs: arias, fas, pga, pgv, sa, duration, sorted_duration
  output_imts:
      - PGA
      - PGV
      - SA
      - duration
      - sorted_duration
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

## Pickers

This section is to configure how the P-wave arrival is estimated. We have found
that for the purposes of splitting the signal and noise windows, the estimated
P-wave arrival time based on the event origin time and a simple 1D velocity
model is more reliable than most alternatives. 

It is important to bear in mind that the error that is of most concern in this
context is an estimate that is too late, which would place some of the signal
energy into the noise window. This would cause otherwise acceptable records to
be rejected. A P-wave estimate that is too early would only have the downside
of shortening the noise window slightly. This motivated the `p_arrival_shift` 
option. This allows you to artificially shift the P-wave by a constsant to
avoid the more problematic late arriving estimate errors.

The reason we keep the alternative pickers that do not rely on travel time 
calculations is because some ground motion data does not have reliable start
times of the record. In these cases, travel time estimates fail and so we fall
back on the alternatives. In this case, the esimate that results in the best
signal-to-noise ratio is used.

Note that the alternative picker algorithms require lots of options and we have
stuck with the default values. We expose the values here to provide flexibility
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
