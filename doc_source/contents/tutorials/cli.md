# Command Line Interface

```{seealso}
Be sure to review the discussion of how the `gmrecords` command line
interface makes use of "projects" in the
{ref}`Initial Setup` section.
```

## The "gmrecords" Command

The primary command line program is called `gmrecords`. This includes a
number of "subcommands," which are described by printing the help message:

```{eval-rst}
.. command-output:: gmrecords -h

```

Note that some of the subcommands with longer names have short aliases to make
the command line calls more concise.

## Project Configuration

For this tutorial, we will create a system-level project.

```
$ gmrecords projects -c
INFO 2021-11-12 18:34:14 | gmrecords.__init__: Logging level includes INFO.
INFO 2021-11-12 18:34:14 | gmrecords.__init__: PROJECTS_PATH: /Users/emthompson/.gmprocess
INFO 2021-11-12 18:34:14 | projects.main: Running subcommand 'projects'
Please enter a project title: [default] tutorial
You will be prompted to supply two directories for this project:
- A *config* path, which will store the gmprocess config files.
- A *data* path, under which will be created directories for each
   event processed.
Please enter the conf path: [/Users/emthompson/gmprocess_projects/tutorial/conf]
Please enter the data path: [/Users/emthompson/gmprocess_projects/tutorial/data]
Please enter your name and email. This information will be added
to the config file and reported in the provenance of the data
processed in this project.
   Name: Eric Thompson
   Email: myemail@email.com

Created project: Project: tutorial
   Conf Path: /Users/emthompson/gmprocess_projects/tutorial/conf
   Data Path: /Users/emthompson/gmprocess_projects/tutorial/data
```

At this point the data has been created but it is empty. The config directory has 
one file in it: `config.yml`. This is the config file that controls many aspects of
how `gmrecords` operates. The user should review the contents and make edits as 
necessary. In some cases, there are usernames and passwords that need to be provided
for some data sources (e.g., CESMD). 

## Download Data

To limit the number of stations in this example, please edit the `config.yml`
file (locaed in the project conf path) to restrict the search radius:

```yaml
FDSNFetcher:
   domain:
      circular:
         maxradius: 0.1
```

Now we will download data by specifying an event ID.

```{tip}
The easiest way to get data for events is by specifying USGS event IDs.
These event IDs can be found by searching for events on the
[Search Earthquake Catalog](https://earthquake.usgs.gov/earthquakes/search/)
page at the USGS. With `gmrecords`, you can specify a single event ID or a
list of event IDs in a text file. Also, you can run customized searches of
the earthquake catalog in python with
[libcomcat](https://github.com/usgs/libcomcat).
```

We will search for records from the 2014 South Napa Earthquake
(event ID
[nc72282711](https://earthquake.usgs.gov/earthquakes/eventpage/nc72282711/executive)).
Note that we have clipped out a bunch of terminal messages regarding the fetcher
connections because those are not important for this tutorial.

```
$ gmrecords download -e nc72282711
INFO 2021-11-12 18:44:19 | gmrecords.__init__: Logging level includes INFO.
INFO 2021-11-12 18:44:19 | gmrecords.__init__: PROJECTS_PATH: /Users/emthompson/.gmprocess
--------------------------------------------------------------------------------
Project: tutorial
   Conf Path: /Users/emthompson/gmprocess_projects/tutorial/conf
   Data Path: /Users/emthompson/gmprocess_projects/tutorial/data
--------------------------------------------------------------------------------
INFO 2021-11-12 18:44:19 | download.main: Running subcommand 'download'
INFO 2021-11-12 18:44:20 | download.main: Number of events to download: 1
INFO 2021-11-12 18:44:20 | download.main: Starting event: nc72282711
...
INFO 2021-11-12 18:45:54 | mass_downloader.download: Downloaded 0.5 MB in total.
```

The downloaded data can be seen in the project data directory

```
$ tree .
.
└── nc72282711
   ├── event.json
   ├── raw
   │   ├── CE.68150..HNE__20140824T102014Z__20140824T102744Z.mseed
   │   ├── CE.68150..HNN__20140824T102014Z__20140824T102744Z.mseed
   │   ├── CE.68150..HNZ__20140824T102014Z__20140824T102744Z.mseed
   │   ├── CE.68150.xml
   │   ├── NC.N016.01.HNE__20140824T102014Z__20140824T102744Z.mseed
   │   ├── NC.N016.01.HNN__20140824T102014Z__20140824T102744Z.mseed
   │   ├── NC.N016.01.HNZ__20140824T102014Z__20140824T102744Z.mseed
   │   ├── NC.N016.xml
   │   ├── NC.NHC..HNE__20140824T102014Z__20140824T102744Z.mseed
   │   ├── NC.NHC..HNN__20140824T102014Z__20140824T102744Z.mseed
   │   ├── NC.NHC..HNZ__20140824T102014Z__20140824T102744Z.mseed
   │   └── NC.NHC.xml
   └── rupture.json
```

From the directory tree above, you can see how `gmrecords` organizes the data
directory:

- within the root data directory there are subdirectories for each event named
  by the event ID,

- within each event directory there is

  - an `event.json` file that stores event information that were retrienved
    from the USGS data,

  - a `raw` directory that holds the downlaoded raw data. In this case, that
    consists of miniseed and StationXML files,

    - The downloaded data is contained within the `raw` directory.
    - The `raw` directory also has PNG files that are plots of the raw data.

  - a `rupture.json` file that includes information about the rupture extent.

## Assemble Data

The `assemble` subcommand collects the data in the raw directory and
organizes it into an ASDF file. We can specify the event ID, but if we
do not then all of the events in the data directory will be assembled.

```
$ gmrecords assemble
INFO 2021-11-12 18:52:58 | gmrecords.__init__: Logging level includes INFO.
INFO 2021-11-12 18:52:58 | gmrecords.__init__: PROJECTS_PATH: /Users/emthompson/.gmprocess
--------------------------------------------------------------------------------
Project: tutorial
   Conf Path: /Users/emthompson/gmprocess_projects/tutorial/conf
   Data Path: /Users/emthompson/gmprocess_projects/tutorial/data
--------------------------------------------------------------------------------
INFO 2021-11-12 18:52:58 | assemble.main: Running subcommand 'assemble'
INFO 2021-11-12 18:52:58 | assemble.main: Number of events to assemble: 1
INFO 2021-11-12 18:52:58 | assemble._assemble_event: Starting event: nc72282711
3 StationStreams(s) in StreamCollection:
3 StationTrace(s) in StationStream (passed):
   NC.N016.01.HNN | 2014-08-24T10:24:08.345000Z - 2014-08-24T10:25:41.740000Z | 200.0 Hz, 18680 samples (passed)
   NC.N016.01.HNZ | 2014-08-24T10:24:08.345000Z - 2014-08-24T10:25:41.740000Z | 200.0 Hz, 18680 samples (passed)
   NC.N016.01.HNE | 2014-08-24T10:24:08.345000Z - 2014-08-24T10:25:41.740000Z | 200.0 Hz, 18680 samples (passed)
3 StationTrace(s) in StationStream (passed):
   NC.NHC..HNE | 2014-08-24T10:20:14.070000Z - 2014-08-24T10:27:44.060000Z | 100.0 Hz, 45000 samples (passed)
   NC.NHC..HNZ | 2014-08-24T10:20:14.070000Z - 2014-08-24T10:27:44.060000Z | 100.0 Hz, 45000 samples (passed)
   NC.NHC..HNN | 2014-08-24T10:20:14.070000Z - 2014-08-24T10:27:44.060000Z | 100.0 Hz, 45000 samples (passed)
3 StationTrace(s) in StationStream (passed):
   CE.68150..HNE | 2014-08-24T10:20:21.000000Z - 2014-08-24T10:22:19.995000Z | 200.0 Hz, 23800 samples (passed)
   CE.68150..HNN | 2014-08-24T10:20:21.000000Z - 2014-08-24T10:22:19.995000Z | 200.0 Hz, 23800 samples (passed)
   CE.68150..HNZ | 2014-08-24T10:20:21.000000Z - 2014-08-24T10:22:19.995000Z | 200.0 Hz, 23800 samples (passed)

INFO 2021-11-12 18:52:59 | stream_workspace.addStreams: Adding waveforms for station N016
INFO 2021-11-12 18:52:59 | stream_workspace.addStreams: Adding waveforms for station NHC
INFO 2021-11-12 18:52:59 | stream_workspace.addStreams: Adding waveforms for station 68150

The following files have been created:
File type: Workspace
   /Users/emthompson/gmprocess_projects/tutorial/data/nc72282711/workspace.h5
```

The console message indicates that the `workspace.h5` ASDF file has been
created.

```{note}
The [Seismic Data](https://seismic-data.org/) folks have developed a
graphical user interface to explore ASDF data sets called
[ASDF Sextant](https://github.com/SeismicData/asdf_sextant)
and this may be useful for browsing the contents of the ASDF file.
Since ASDF is an HDF5 specification, it can also be loaded in most
programming languages using
[HDF5](https://www.hdfgroup.org/solutions/hdf5/) libraries.
```

## Process Waveforms

The `process_waveforms` (or just `process` for short) subcommand reads in
the raw data from the ASDF workspace files that were created by the assemble
subcommand, and then applies the waveform processing steps that are specified
the config file (in the processing section). The processed waveforms are then
added to the ASDF workspace file.

```
$ gmrecords process
INFO 2021-11-12 18:54:40 | gmrecords.__init__: Logging level includes INFO.
INFO 2021-11-12 18:54:40 | gmrecords.__init__: PROJECTS_PATH: /Users/emthompson/.gmprocess
--------------------------------------------------------------------------------
Project: tutorial
   Conf Path: /Users/emthompson/gmprocess_projects/tutorial/conf
   Data Path: /Users/emthompson/gmprocess_projects/tutorial/data
--------------------------------------------------------------------------------
INFO 2021-11-12 18:54:40 | process_waveforms.main: Running subcommand 'process_waveforms'
INFO 2021-11-12 18:54:40 | process_waveforms.main: Processing tag: default
INFO 2021-11-12 18:54:40 | process_waveforms._process_event: Processing 'unprocessed' streams for event nc72282711...
INFO 2021-11-12 18:54:40 | processing.process_streams: Stream: CE.68150.HN
INFO 2021-11-12 18:54:41 | processing.process_streams: Finished processing streams.
INFO 2021-11-12 18:54:41 | process_waveforms._process_event: Processing 'unprocessed' streams for event nc72282711...
WARNING 2021-11-12 18:54:41 | phase.calc_snr: Noise window for NC.N016.01.HNE has mean of zero.
WARNING 2021-11-12 18:54:41 | phase.calc_snr: Noise window for NC.N016.01.HNN has mean of zero.
WARNING 2021-11-12 18:54:41 | phase.calc_snr: Noise window for NC.N016.01.HNZ has mean of zero.
INFO 2021-11-12 18:54:41 | processing.process_streams: Stream: NC.N016.HN
WARNING 2021-11-12 18:54:41 | warnings._showwarnmsg: /Users/emthompson/miniconda/envs/gmprocess/lib/python3.8/site-packages/obspy/core/inventory/response.py:1895: UserWarning: More than one PolesZerosResponseStage encountered. Returning first one found.
warnings.warn(msg)
INFO 2021-11-12 18:54:41 | stationtrace.fail: snr_check - NC.N016.01.HNE - Failed SNR check; SNR less than threshold.
INFO 2021-11-12 18:54:41 | stationtrace.fail: snr_check - NC.N016.01.HNN - Failed SNR check; SNR less than threshold.
INFO 2021-11-12 18:54:41 | stationtrace.fail: snr_check - NC.N016.01.HNZ - Failed SNR check; SNR less than threshold.
INFO 2021-11-12 18:54:41 | processing.process_streams: Finished processing streams.
INFO 2021-11-12 18:54:41 | process_waveforms._process_event: Processing 'unprocessed' streams for event nc72282711...
INFO 2021-11-12 18:54:42 | processing.process_streams: Stream: NC.NHC.HN
INFO 2021-11-12 18:54:42 | stationtrace.fail: check_tail - NC.NHC..HNE - Velocity ratio is greater than 0.3
INFO 2021-11-12 18:54:42 | stationtrace.fail: check_tail - NC.NHC..HNE - Displacement ratio is greater than 0.6
INFO 2021-11-12 18:54:42 | processing.process_streams: Finished processing streams.
INFO 2021-11-12 18:54:42 | stream_workspace.addStreams: Adding waveforms for station 68150
INFO 2021-11-12 18:54:43 | stream_workspace.addStreams: Adding waveforms for station N016
INFO 2021-11-12 18:54:43 | stream_workspace.addStreams: Adding waveforms for station NHC
No new files created.
```

Note that the console messages indicate that some of the traces failed the
signal-to-noise requirements.

## Generate Report

For each event, the `gmrecords` command can generate a PDF report. The report
is useful to review which streams failed and why. The report gives a 1-page per
station summary that includes:

- the acceleration, velocity, and displacement plots,
- the location where the signal and noise windows were split,
- the signal and noise spectra (raw and smoothed), and
- a table of the processing steps applied to the record.
- the failure reason for stations that have failed.
- shaded green regions that show range in acceptable amplitudes in the tail
  of the trace for a "sanity" check; this check is designed to remove records
  with unnatural drifts in the waveform.

```
$ gmrecords report
INFO 2021-11-12 18:57:54 | gmrecords.__init__: Logging level includes INFO.
INFO 2021-11-12 18:57:54 | gmrecords.__init__: PROJECTS_PATH: /Users/emthompson/.gmprocess
--------------------------------------------------------------------------------
Project: tutorial
   Conf Path: /Users/emthompson/gmprocess_projects/tutorial/conf
   Data Path: /Users/emthompson/gmprocess_projects/tutorial/data
--------------------------------------------------------------------------------
INFO 2021-11-12 18:57:54 | generate_report.main: Running subcommand 'generate_report'
INFO 2021-11-12 18:57:54 | generate_report.generate_diagnostic_plots: Creating diagnostic plots for event nc72282711...
INFO 2021-11-12 18:58:00 | generate_report.main: Generating summary report for event nc72282711...

The following files have been created:
File type: Moveout plot
   /Users/emthompson/gmprocess_projects/tutorial/data/nc72282711/moveout_plot.png
File type: Summary report
   /Users/emthompson/gmprocess_projects/tutorial/data/nc72282711/tutorial_default_report_nc72282711.pdf
```

From the report plots (see below), you can see that the NC.N016 station failed
the SNR check. You can also see that it is likely because the signal and noise
windows were not cleanly separated and so if the windowing were adjusted this
record might pass the signal-to-noise requirement. Additionally, you can see
the large unnatural drifts present in the velocity and displacement records
that the tail check is designed to avoid. In this case, the code never applies
the talk check (and so the green regions are not labeled) because the record
failed the signal-to-noise ratio test first.


```{tab} NC.NHC
<img src="../../_static/nc72282711_NC.NHC.HN.png" alt="NC.NHC.HN">
```

```{tab} NC.N016
<img src="../../_static/nc72282711_NC.N016.HN.png" alt="NC.N016.HN">
```

```{tab} CE.68150
<img src="../../_static/nc72282711_CE.68150.HN.png" alt="CE.68150.HN">
```


```{admonition} Report Explanation
:class: note

The full report for each station also includes the provenance table and 
failure reason (not shown here). The **first row** of plots is the
acceleration time series, the **second row** of plots is the velocity time
series. The vertical dashed red line indicates the boundary between the
signal and noise windows. The **third row** of plots is the displacement
time series. The **fourth row** of plots gives the raw and
smoothed Fourier amplitude spectra, where the dashed black curve is a Brune
spectra fit to the data, and the vertical dashed line is the corner
frequency. The **fifth row** of plots is the signal-to-noise ratio (SNR),
where the vertical grey lines indicate the bandpass where the SNR criteria
are required, the horizontal grey line is the minimum SNR, and the vertical
black dashed lines are the selected bandpass filter corners.
```

## Compute Station Metrics

The `compute_station_metrics` subcommand computes station metrics (like
epicentral distance) and add them to the ASDF workspace file.

```
$ gmrecords compute_station_metrics
INFO 2021-11-12 19:07:18 | gmrecords.__init__: Logging level includes INFO.
INFO 2021-11-12 19:07:18 | gmrecords.__init__: PROJECTS_PATH: /Users/emthompson/.gmprocess
--------------------------------------------------------------------------------
Project: tutorial
   Conf Path: /Users/emthompson/gmprocess_projects/tutorial/conf
   Data Path: /Users/emthompson/gmprocess_projects/tutorial/data
--------------------------------------------------------------------------------
INFO 2021-11-12 19:07:18 | compute_station_metrics.main: Running subcommand 'compute_station_metrics'
INFO 2021-11-12 19:07:18 | compute_station_metrics._event_station_metrics: Computing station metrics for event nc72282711...
INFO 2021-11-12 19:07:18 | compute_station_metrics._event_station_metrics: Calculating station metrics for CE.68150.HN...
INFO 2021-11-12 19:07:18 | compute_station_metrics._event_station_metrics: Added station metrics to workspace files with tag 'default'.
INFO 2021-11-12 19:07:18 | compute_station_metrics._event_station_metrics: Calculating station metrics for NC.N016.HN...
INFO 2021-11-12 19:07:18 | compute_station_metrics._event_station_metrics: Added station metrics to workspace files with tag 'default'.
INFO 2021-11-12 19:07:18 | compute_station_metrics._event_station_metrics: Calculating station metrics for NC.NHC.HN...
INFO 2021-11-12 19:07:18 | compute_station_metrics._event_station_metrics: Added station metrics to workspace files with tag 'default'.
No new files created.
```

## Compute Waveform Metrics

The `compute_waveform_metrics` subcommand computes waveform metrics (such as
spectral accelerations) and adds them to the ASDF workspace file. The waveform
metrics that are computed are defined in the metrics section of the conf file.
The metrics are defined by intensity metric types (e.g., spectral acceleration
vs duration) and intensity measure component (how the instrument components are
combined).

```
$ gmrecords compute_waveform_metrics
INFO 2021-11-12 19:09:10 | gmrecords.__init__: Logging level includes INFO.
INFO 2021-11-12 19:09:10 | gmrecords.__init__: PROJECTS_PATH: /Users/emthompson/.gmprocess
--------------------------------------------------------------------------------
Project: tutorial
   Conf Path: /Users/emthompson/gmprocess_projects/tutorial/conf
   Data Path: /Users/emthompson/gmprocess_projects/tutorial/data
--------------------------------------------------------------------------------
INFO 2021-11-12 19:09:10 | compute_waveform_metrics.main: Running subcommand 'compute_waveform_metrics'
INFO 2021-11-12 19:09:10 | compute_waveform_metrics._compute_event_waveform_metrics: Computing waveform metrics for event nc72282711...
INFO 2021-11-12 19:09:10 | compute_waveform_metrics._compute_event_waveform_metrics: Calculating waveform metrics for CE.68150.HN...
INFO 2021-11-12 19:09:13 | compute_waveform_metrics._compute_event_waveform_metrics: Adding waveform metrics to workspace files with tag 'default'.
No new files created.
```

Note that you can see from the console output that the waveform metrics were
not computed for the station that failed the signal-to-noise ratio test.

## Export Failure Tables

It is useful to summarize the reasons that records have failed the QA checks,
and this information can be output in a spreadsheet using the
`export_failure_tables` subcommand. Unlike many of the other
subcommands, the output combines the results in all project events and puts
the result into the base project directory.

```
$ gmrecords export_failure_tables
INFO 2021-11-12 19:10:43 | gmrecords.__init__: Logging level includes INFO.
INFO 2021-11-12 19:10:43 | gmrecords.__init__: PROJECTS_PATH: /Users/emthompson/.gmprocess
--------------------------------------------------------------------------------
Project: tutorial
   Conf Path: /Users/emthompson/gmprocess_projects/tutorial/conf
   Data Path: /Users/emthompson/gmprocess_projects/tutorial/data
--------------------------------------------------------------------------------
INFO 2021-11-12 19:10:43 | export_failure_tables.main: Running subcommand 'export_failure_tables'
INFO 2021-11-12 19:10:43 | export_failure_tables.main: Creating failure tables for event nc72282711...

The following files have been created:
File type: Failure table
   /Users/emthompson/gmprocess_projects/tutorial/data/nc72282711/tutorial_default_failure_reasons_short.csv
File type: Complete failures
   /Users/emthompson/gmprocess_projects/tutorial/data/tutorial_default_complete_failures.csv
```

## Export Metric Tables

Although the metrics can be accessed directly from the ASDF file, it is often
convenient to save the metrics (both station and waveform) into a "flatfile"
where each row corresponds to a single record.

```
$ gmrecords export_metric_tables
INFO 2021-11-12 19:11:38 | gmrecords.__init__: Logging level includes INFO.
INFO 2021-11-12 19:11:38 | gmrecords.__init__: PROJECTS_PATH: /Users/emthompson/.gmprocess
--------------------------------------------------------------------------------
Project: tutorial
   Conf Path: /Users/emthompson/gmprocess_projects/tutorial/conf
   Data Path: /Users/emthompson/gmprocess_projects/tutorial/data
--------------------------------------------------------------------------------
INFO 2021-11-12 19:11:38 | export_metric_tables.main: Running subcommand 'export_metric_tables'
INFO 2021-11-12 19:11:38 | export_metric_tables.main: Creating tables for event nc72282711...

The following files have been created:
File type: Metric tables
   /Users/emthompson/gmprocess_projects/tutorial/data/tutorial_default_events.csv
   /Users/emthompson/gmprocess_projects/tutorial/data/tutorial_default_metrics_rotd50.0.csv
   /Users/emthompson/gmprocess_projects/tutorial/data/tutorial_default_metrics_h2.csv
   /Users/emthompson/gmprocess_projects/tutorial/data/tutorial_default_metrics_z.csv
   /Users/emthompson/gmprocess_projects/tutorial/data/tutorial_default_metrics_h1.csv
   /Users/emthompson/gmprocess_projects/tutorial/data/tutorial_default_metrics_rotd50.0_README.csv
   /Users/emthompson/gmprocess_projects/tutorial/data/tutorial_default_metrics_h2_README.csv
   /Users/emthompson/gmprocess_projects/tutorial/data/tutorial_default_metrics_z_README.csv
   /Users/emthompson/gmprocess_projects/tutorial/data/tutorial_default_metrics_h1_README.csv
   /Users/emthompson/gmprocess_projects/tutorial/data/tutorial_default_fit_spectra_parameters.csv
   /Users/emthompson/gmprocess_projects/tutorial/data/tutorial_default_fit_spectra_parameters_README.csv
   /Users/emthompson/gmprocess_projects/tutorial/data/tutorial_default_snr.csv
   /Users/emthompson/gmprocess_projects/tutorial/data/tutorial_default_snr_README.csv
```

Note that the metric tables are organized into separate files for each intensity
measure component (i.e., "IMT").

## Export Provenance Tables

As with the metric and failure tables, you can also output tables summarzing
the provenance information.

```
$ gmrecords export_provenance_tables
INFO 2021-11-12 19:13:00 | gmrecords.__init__: Logging level includes INFO.
INFO 2021-11-12 19:13:00 | gmrecords.__init__: PROJECTS_PATH: /Users/emthompson/.gmprocess
--------------------------------------------------------------------------------
Project: tutorial
   Conf Path: /Users/emthompson/gmprocess_projects/tutorial/conf
   Data Path: /Users/emthompson/gmprocess_projects/tutorial/data
--------------------------------------------------------------------------------
INFO 2021-11-12 19:13:00 | export_provenance_tables.main: Running subcommand 'export_provenance_tables'
INFO 2021-11-12 19:13:00 | export_provenance_tables.main: Creating provenance tables for event nc72282711...

The following files have been created:
File type: Provenance
   /Users/emthompson/gmprocess_projects/tutorial/data/nc72282711/tutorial_default_provenance.csv
```

## Generate Regression Plot

Although the report created by the `generate_report` subcommand is helpful
for checking for some possible processing problems, it cannot identify
outliers that may be due to incorrect metadata (such as the gain). This type
of issue is relatively common, and can sometimes be identified by plotting
the peak ground acceleration as a function of distance.

```
$ gmrecords generate_regression_plot
INFO 2021-11-12 19:14:01 | gmrecords.__init__: Logging level includes INFO.
INFO 2021-11-12 19:14:01 | gmrecords.__init__: PROJECTS_PATH: /Users/emthompson/.gmprocess
--------------------------------------------------------------------------------
Project: tutorial
   Conf Path: /Users/emthompson/gmprocess_projects/tutorial/conf
   Data Path: /Users/emthompson/gmprocess_projects/tutorial/data
--------------------------------------------------------------------------------
INFO 2021-11-12 19:14:01 | generate_regression_plot.main: Running subcommand 'generate_regression_plot'

The following files have been created:
File type: Multi-event regression plot
   /Users/emthompson/gmprocess_projects/tutorial/data/regression_rotd50.0_PGA.png
```

An example is given below, but for this plot we've re-run the above commands
with a larger search radius to make the plot look a little bit more interesting
than it would have looked with the smaller search radius.

```{figure} ../../_static/regression_rotd50.0_PGA.png
Example "regression" plot.
```

## Station Map

The `generate_station_maps` command makes an interactive HTML map that can be opened in a browser.

```
$ gmrecords generate_station_maps
INFO 2021-11-12 19:45:55 | gmrecords.__init__: Logging level includes INFO.
INFO 2021-11-12 19:45:55 | gmrecords.__init__: PROJECTS_PATH: /Users/emthompson/.gmprocess
--------------------------------------------------------------------------------
Project: tutorial
   Conf Path: /Users/emthompson/gmprocess_projects/tutorial/conf
   Data Path: /Users/emthompson/gmprocess_projects/tutorial/data
--------------------------------------------------------------------------------
INFO 2021-11-12 19:45:55 | generate_station_maps.main: Running subcommand 'generate_station_maps'
INFO 2021-11-12 19:45:55 | generate_station_maps.main: Generating station maps for event nc72282711...
INFO 2021-11-12 19:46:05 | stationtrace.fail: __check_channels - NC.RWSVT.01.HN2 - Nonunique channel code in StationStream.
INFO 2021-11-12 19:46:05 | stationtrace.fail: __check_channels - NC.RWSVT.01.HNZ - Nonunique channel code in StationStream.
INFO 2021-11-12 19:46:05 | stationtrace.fail: __check_channels - NC.RWSVT.03.HNE - Nonunique channel code in StationStream.
INFO 2021-11-12 19:46:05 | stationtrace.fail: __check_channels - NC.RWSVT.03.HNN - Nonunique channel code in StationStream.
INFO 2021-11-12 19:46:05 | stationtrace.fail: __check_channels - NC.RWSVT.03.HNZ - Nonunique channel code in StationStream.

The following files have been created:
File type: Station map
   /Users/emthompson/gmprocess_projects/tutorial/data/nc72282711/stations_map.html
```

<figure class="align-default" id="int_stn_map">
   <iframe
      src="../../_static/stations_map.html"
      title="Example interactive station map"
      style="width:100%; height:300px;"
   ></iframe>

   <figcaption>
      <p>
         <span class="caption-text">Example interactive station map.</span>
         <a class="headerlink" href="#int_stn_map" title="Permalink to this image">#</a>
      </p>
   </figcaption>
</figure>


% Indices and tables

% ==================

% * :ref:`genindex`

% * :ref:`modindex`

% * :ref:`search`
