# Changelog

## Updates since most recent release

- Adding "Merge Request Guidelines" and "Release Steps" sections to developer resources. 
- Improve projects subcommand.
  - Always prompt for names of 'data' and 'conf' directories with reasonable defaults.
  - Provide appropriate error message when attempting to list, switch, or delete projects when none exist.
  - Allow use of projects subcommand from Python scripts.
- Fixes SAC format units conversion issue. 
- Add lp_max option for lowpass_max_frequency method.

## 1.2.1 / 2022-10-04

- Data fetcher bugfix.
- Improvement to Windows install instructions.
- Add changelog.
- Add "config" subcommand to gmrecords.
- Fix pandas to_latex warning.
- Add check_stream config section with any_trace_failures key. 
- Modify StationID column in metric tables to include full channel code when available. 
- Move C code to esi-core repository.
- Added rename project flag for gmrecords proj subcommand
- Switched from os.path to Pathlib in projects.py and gmrecords.py

## 1.2.0 / 2022-08-15

- First release with wheels uploaded to pypi.
- Major reorganization of code, putting the base package inside src/. 
- Replace dask with concurrent.futures
- Factor out pkg_resources
- Remove support for Vs30 (because it adds too many dependencies)
- Fix code version method and add DATA_DIR to constants
- Changed setup to use pyproject.toml and setup.cfg; still need setup.py but only for
  cython stuff.
- Factor out use of libcomcat.
- Added "magnitude" and "none" options for the method argument to signal_end function.
- Make processing steps auto detected via decorators.
- Reorganize processing step modules.
- Resolve a lot of future warnings.
- In config, replace "do_check" with "enabled" for a more consistent naming convention
  across config sections.
- Reorganiztaion of config structure to allow for parameters to be unspecified and thus
  use the default values from the associated methods. 
- More gracefully handle cases where workspace file does not exist but is expected.
- Add label arg to gmconvert.
- Make colocated selection optional.
- Replace stastic map with interactive HTML map and add to CLI tutorial in documentation.
- Remove cartopy dependency.
- Get scnl from COSMOS comments.
- Add freq differentiation option.
- Ignore lowpass_max_frequency step if manually set.
- Add support for UCLA manually selected lowpass corners
- Update CEUS network in COSMOS Table 4
- Reorganize FDSN config options to better match the respective obspy functions.
- Add support for frequency domain filtering.
- Add support for frequency domain integration.
- Turn off logging to stream if using log file and allow user specified filename for 
  logging.
- Apply min freq criteria to high pass filter. 
- Fix confusion between 'unit_types' and 'units'.
- Adding in code to handle Taiwan data script.
- Added cosmos writer.
- Remove legacy "gmsetup" command.
- Reduced redundancy in the first three steps of MetricsController.execute_steps.
- Allow for magnitude-distance-based channel prefrence order.
- Added config to ASDF and read it from there rather than file system if it exists.
- Replaced pyyaml with ruamel.yaml because the latter is actively maintained and 
  allows persistent comments.
- Store noise time series in output ASDF file.

## 1.1.10 / 2021-09-21

- Add ANN clipping code and test.

## 1.1.9 / 2021-09-20

- Fix ExponentialSmoothing future warning
- Remove legacy "gmprocess2" command.
- Relax dependency versions.
- Fix jerk unit tests.

## 1.1.8 / 2021-07-19

- Added the auto_shakemap subcommand
- Bugfix to CESMD fetcher
- Improved handling of nans and empty data structures
- Simplified error logging
- Added "sorted duration" metric
- Changed unknown network to '/' rather than 'ZZ'
- Added event id to output filenames where appropraite
- Improved efficiency by removing calls to trace.times()
- Optimized distance calculations
- Fix behavior when no project has been configured
- Added a linear mixed effects tutorial to the docs
- Removed unnecessary processing steps that we occurring in the download subcommand
- Added a method for finding USGS event id from other projects and included a table 
  for cross referencing event IDs.
- Changed location of temp directory used for reading in data.

## 1.1.7 / 2020-12-20

- More updates to try to support Windows OS and build with conda.

## 1.1.6 / 2020-12-17

- More updates to try to support Windows OS.

## 1.1.3 / 2020-12-11

- Fixed precision of SA strings in shakemap output json.
- Add Windows install script and some refactoring to try to support Windows OS.
- Renamed io/fdsn to io/obspy.

## 1.1.2 / 2020-08-31

- Fixes to c compiler issues.

## 1.1.0 / 2020-08-30

- Instrument response correction will now always try to use poles/zeros to remove 
  response, and only use the simpler sensitivity method if no poles/zeros are available.
- The pattern matching on excluding FDSN records is improved to better handle wildcards, 
  and can be applied to channel, network, station, and location codes.
- Fixed a bug where zeros could be returned by the Konno-Omachi smoothing algorithm. 
  Now it will return nans if there's no point within the smoothing window, and there's 
  an option to zero-pad the data to ensure that there are points in all windows.
- Fixed bug in Raoof et al. attention model (that is used for fitting a Brune spectra 
  to the signal spectra)
- Added a goodness-of-fit measure of the Brune spectra to the signal spectra.
- Fixed bug in station map that allowed the extent to be too small if there's only one 
  station and it is very close to the earthquake.
- Fixed bugs in code for reading the workspace file into Matlab that arose because it 
  was not kept up to date with other changes in the code.
- Relaxed the restrictions placed on the allowed IMT/IMC combinations.
- Fixed a bug in how the upsampling was done when computing high-frequency response 
  spectra. The code now does the full upsampling method as recommended by Boore and 
  Goulet (2014; DOI 10.1007/s10518-013-9574-9), and we added a test of low sample rate 
  records against the high-frequency response spectra reported by NGA East for the same 
  record.

## 1.0.4 / 2020-03-25

- Fix handling sensitivity units other than meters.
- Added optional p_arrival_shift parameter to allow users to shift signal split time
  left or right as needed.
- General optimization.

## 1.0.3 / 2020-01-13

- Minor config tweaks.
- Modified Turkey/KNET fetchers to handle cases where no earthquakes are found.
- Exit gracefully when no data is found.
- Added Geonet near real-time url to list of FDSN services when event is less than 7 
  days old.
- Added CESMD fetcher. 
- Added matlab functions for reading ASDF and documentation.
- Allow for setting the precision of data tables.

## 1.0.2 / 2019-10-17

- Now using ASDF dataset ifilter() method to speed up search times for waveforms in 
  HDF files.
- Improved windowing to remove signal from multiple events in the same waveform.
- Added moveout plots to summary report.
- Improved spectral fitting.
- Add QA checks for multiple events.

## 1.0.1 / 2019-09-30

- Adding reader/tests for Chilean (Renadic network) format.
- Documentation fixes.

## 1.0.0 / 2019-09-25

- Initial release.


