# Configuration File

The config file is the primary means by which users can adjust and customize
*gmprocess*. 

The default config file in the source code includes comments to help explain the values
and their units
[here](https://github.com/usgs/groundmotion-processing/blob/master/gmprocess/data/config_production.yml).
This is a useful reference because sections or comments can be removed from the
config file for a given project. 

When a project is created, it has an associated "config directory." The project
creation project will create a single file: 

```
conf/
└── user.yml
```

Any `*.yml` files in this directory will be merged with the default config that is in 
source code repository. The reason for this system is that (1) we don't want to
overwrite your customized config when the code is updated, and (2) by merging your 
project config into the default config, we should avoid breaking functionality that
relies on config updates.

The following sections correspond to the top-level sections of the config file.
Click on the section for more details. 

In many cases, you may want to turn off or turn on specific fetchers. This is done
with the `enabled` key within each fetcher. For example, to turn off the a fetcher 
you would need to add the following code to a `*.yml` in the project conf directory:

```
fetchers:
    KNETFetcher:
        enabled: False
```

Note that the name of the config file doesn't matter. You can put this in the `user.yml` 
file or into another file, whatever is most convenient for you. For example, it might
be convenient to organize the config files by the top level sections:

```
conf/
├── user.yml
├── fetchers.yml
├── windows.yml
...
└── processing.yml
```

The `processing` section behaves somewhat differently than other sections because it is
how you control the pocessing steps. In many cases, processing steps must be repeated,
such as the `detrend` step. Here is an exmaple of the processing section that specifies
the processing steps but does not specify any of the function arguments except for the
`detrend` step:

```yaml
processing:
    - check_free_field:
    - check_instrument:
    - min_sample_rate:
    - check_clipping:
    - detrend:
        detrending_method: linear
    - detrend:
        detrending_method: demean
    - remove_response:
    - detrend:
        detrending_method: linear
    - detrend:
        detrending_method: demean
    - compute_snr:
    - snr_check:
    - get_corner_frequencies:
    - lowpass_max_frequency:
    - cut:
    - taper:
    - highpass_filter:
    - lowpass_filter:
    - detrend:
        detrending_method: pre
    - detrend:
        detrending_method: baseline_sixth_order
    - fit_spectra:
```

The more complex structure in this section is necessary so that you can modify the
steps that are used and their order. Thus, in this section, you turn off a step by
deleting it's entry.

To see the available arguments for each step and their default values, you can look
up the function in the `gmprocess/waveform_processing` directory 
([here](https://github.com/usgs/groundmotion-processing/tree/main/gmprocess/waveform_processing)
is the link to it in GitHub). 

```{Hint}
If you are familiar with python, you'll note that each available processing step is
marked with the `@ProcessingStep` decorator. 
```

Many sections of the config file are not of interest to most uses, such as the details
of the `pickers` section. However, the `p_arrival_shift` value is very useful if you
are collecting data in a region where the travel time picks are often later than the
actual p-wave arrival, causing some of the shaking to be placed in the "noise" window,
which in tern causes the record to fail the signal-to-noise ratio test.

Please post any questions or issues that you have regarding the config to the GitHub
[issues](https://github.com/usgs/groundmotion-processing/issues) page. 

% Indices and tables

% ==================

% * :ref:`genindex`

% * :ref:`modindex`

% * :ref:`search`
