# gmprocess Python script

The `gmprocess` script has one *required* and many *optional* parameters. The
required argument is:
* `--output-directory` (or `-o`) -- An output directory that will contain
  subdirctories that correspond to each event. 

The steps to perform are controlled by the following arguments:

* `--assemble` Download data from available online sources or load raw
  data from files if the `--directory` is provided. Adds the data to
  the workspace and makes plots of the unprocessed waveforms in the
  `raw` directory.
* `--process` Process data using steps defined in the configuration
  file. Add the processed waveforms, waveform metrics, and station
  metrics to the workspace.
* `--report` Create a summary report for each event specified,
  including a map of stations and for each station plots of
  acceleration and velocity waveforms, response spectra, and a list of
  the processing steps performed.
* `--provenance` Generate a provenance table listing the steps applied
  to each waveform in the format specified by the `--format` argument.
* `--export` Generate a series of metric tables (NGA-style "flat" file) for all
  events and intensity metric components. One table is generated per
  intensity metric component (IMC) with columns containing station
  information and intensity measure type (IMT).
* `--shakemap` Generate ShakeMap-friendly peak ground motions table
  that can be used as input to ShakeMap (may be deprecated in the future).

Some steps have prerequisites. For example, `--process` requires
`--assemble` to have run previously. Similarly, `--report`, `--provenance`,
`--export`, and `--shakemap` all require `--process` to have run previously.

The first step is to "assemble" the data into an output directory where the
data are placed in the ASDF file format, which is the primary purpose of the
`--assemble` argument. When using the `--assemble` argument there are two
different ways in which the data can be assembeled: either by retrieving data from
online sources, or by specifying a local directory (specified as the `--directory`
argument) where data has already been downloaded. 

When assembling data from online sources (i.e., the `--directory` argument is not
set), the event information must be specified using one of the following arguments:

* `--eventids EVID1 .. ENIDN` Specify 1 to many ComCat event IDs;
* `--textfile FILENAME` Specify a text file with *either* a list of
  ComCat IDs or space separated values of `ID`,`TIME`, `LAT`, `LON`,
  `DEPTH`, `MAG`;
* `--eventinfo ID TIME LAT LON DEPTH MAG`

If assembing data from a local directory (specified with the `--directory`). 
Lets call this path `proj_dir`, and it must contain a separate directory for each
event, where the event directory name is the event ID, within which the data is
placed in a directory named "raw". For example, if you have data for event ID
"abc123" then the data for that event should be placed in
`proj_dir/abc123/raw/`.

Other arguments controlling behavior include:

* `--format FORMAT` Format for tabular output (`csv` or `excel`, default=`csv`)
* `--process-tag TAG` Tag associated with processed data. If not
  specified, the tag is set to the current date/time in YYYYMMDDHHMMSS format.
* `--config FILENAME` Specify the configuration to use. If not
  specified, a default configuration is used.
* `--recompute-metrics` Recompute the metrics; usually used in
  conjunction with `--config` with a different set of metrics.
* `--log-file FILENAME` Specify filename for the logging information
  normall sent to stdout.
* `--debug` 
* `--quiet`


## gmprocess Output

Running gmprocess will generate a nested data structure. For example, the command:

```bash
gmprocess --output-directory=data/nocal \
    --assemble \
    --process \
    --report \
    --provenance \
    --export \
    --eventids nc72282711 nc72507396
```
 will result in a directory structure that looks like this:
```
 data/nocal
            |
            +-- *.csv (IMC tables, plus events.csv)
            +-- <CHOSENIMC_CHOSEN_IMT>.png (regression plot)
            |    
            +-- nc72282711
            |  |  
            |  +-- report_nc72282711.pdf
            |  +-- stations_map.png
            |  +-- workspace.hdf
            |  +-- provenance.csv
            |  +-- raw
            |      |
            |      +--(raw data files)
            |      +--(PNG plots of raw data files, grouped by station)
            |   
            |  +-- plots
            |      |
            |      +--(diagnostic plots of each waveform)
            +-- nc72507396
            |  |  
            |  +-- report_nc72507396.pdf
            |  +-- stations_map.png
            |  +-- workspace.hdf
            |  +-- provenance.csv
            |  +-- raw
            |      |
            |      +--(raw data files)
            |      +--(PNG plots of raw data files, grouped by station)
            |  +-- plots
            |      |
            |      +--(diagnostic plots of each waveform)
```
