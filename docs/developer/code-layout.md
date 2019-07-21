# Code layout

## Root directory

- The root directory contains basic information files, such as `README`
  and `LICENSE.md`. 
- Command line programs are located in the `bin` directory.
- The main package with the code is called `gmprocess`. 
- Unit tests are located in the `tests` directory, and we have organized the
  subdirectories here to mimic the directory structure of the rest of the
  repository (e.g., there are `bin` and `gmprocess` subdirectories).

## gmprocess

The `gmprocess` package a number of modules which are parimarily for basic
processing steps that get imported/used by command line programs or other
modules. A few modules at this level are worth highlighting:

- `processing.py` includes the `process_streams` method that is the driver
  for most of the waveform processing steps.
- `stationtrace.py` is where we define the `StationTrace` subclass ObsPy's
  `Trace` class.
- `stationstream.py` is where we define the `StationStream` subclass of
  ObsPY's `Stream` class.
- `streamcollection.py` is where we deinfe the `StreamCollection` class,
  which is basically a list of StationStream objects, where the constituent
  StationTraces are grouped such the traces within each StattionStream are
  from the same network/station/instrument, and some consistency checks are
  applied to the data.

## gmprocess/io

Input/output methods are contained in the `io` package. There are sub-packages
for different methods (e.g., `cosmos`, `geonet`). The module `read.py`
inclues the `read_data` method that auto-detects the data format and returns
a list of `StationStream` objects.

## gmprocess/metrics

The station and waveform metric code is in the `metrics` package.

Waveform metric calculations start with the `MetricsController` class,
defined in the `metrics_controller.py` module. The results are encapsulated
in the `StationSummary` class, defined in `station_summary.py`, which contains
some convenience methods.



