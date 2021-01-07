# Configuration

The primary method for specifying parameters is a configuration file in the [Yet Another Markup Language (YAML)](https://yaml.org/). A default configuration file [gmprocess/data/config.yml](https://github.com/usgs/groundmotion-processing/blob/master/gmprocess/data/config.yml) is bundled with the code.

You can generate a custom copy of this configuration file using the `gmsetup`
program:

```
$ gmsetup --help

usage: gmsetup [-h] [-d | -q] [-f FULL_NAME [FULL_NAME ...]] [-e EMAIL] [-l]
               [-s SECTIONS [SECTIONS ...]] [-o]
               config_file

Setup gmprocess config files.

positional arguments:
  config_file           Path to desired output config file.

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Print all informational messages.
  -q, --quiet           Print only errors.
  -f FULL_NAME [FULL_NAME ...], --full-name FULL_NAME [FULL_NAME ...]
                        Supply the config with your name
  -e EMAIL, --email EMAIL
                        Supply the config with your email address
  -l, --list-sections   List the sections in the config and exit.
  -s SECTIONS [SECTIONS ...], --sections SECTIONS [SECTIONS ...]
                        Supply list of section names to include in output
                        file.
  -o, --overwrite       Overwrite existing config file at the same location.
```

## Sections in the configuration file

### fetchers

See "Fetching Data" section of the documentation.

### read

This section is for options when reading data. Currently we only have one option:

* `resample_rate` -- This is only used for data from older analog instruments that
   have been manually digitized and has uneven sample spacings. Currently we only
   support linear interpolation of unevent samples.

### windows


This section controls options regarding how the signal and noise windows are
selected. See the "Windowing data" subsection under "Processing steps" for
additional details.


### processing

This section is for processing steps that will affect the waveform and get
recorded as seismological provenance data. There are many available processing
steps, and the steps can be delete, commented out, and rearranged.

Please see the example config file for the list of supported steps, examples
of their use, and explanation of each step, as well as the "Waveform processing"
subsection under "Processing steps" for additional details.


### colocated

This section provides options for how to handle colocated instruments.

### duplicate

This section is for handling duplicate data. This comes up when a data center
provides the same data in multiple file formats, or when the same data is
provided by multiple data centers.

Since network codes are not reported reliably, we include methods for detecting
duplicates that does not rely on the network code being accurate. Options
include:

* `max_dist_tolerance` -- Maximum distance tolerance (in m) for duplicate data.

* `process_level_preference` -- Preference for selecting process level when
  faced with duplicate data but with different processing levels. Must be a list
  containing 'V0', 'V1', and 'V2'. The first item is the most preferred, and the
  last item is the least preferred.

* `format_preference` -- Analogous to process level preference, but for file
  formats. 


### build_report

This is for building a report, with a one-page summary of the data in each
StationStream per page. It will write out the latex file, and then look for
the `pdflatex` command and attempt to build the pdf. This requires
`summary_plots` to have been run. Currently we only support the `latex`
format but we expect to expand this in the near future.

### metrics

This section is for calculating waveform metrics and allows one to set
the output intensity measure types (IMTs) and output intensity measure
components (IMCs). See the comments in the config file for additional
explanation.

### pickers

This section is for options regarding the estimation of seismic phases,
which are used for setting the start time of the signal window. By
default, we first use use the travel time calculations given a 1D
velocity model, as implemented in teh `taup` package of ObsPy.

If the travel time calculation results in an arrival time prior to the
start of the record, then the other picker methods are evalulated, then
the other methods are evaluated and the one that results in the largest
signal-to-noise ration is preferred. 

