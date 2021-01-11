Command Line Interface
======================

.. seealso::

   Be sure to review the discussion of how the ``gmrecords`` command line 
   interface makes use of "projects" in the 
   :ref:`Initial Setup` section.

The gmrecords command
---------------------

The primary command line program is called ``gmrecords``. This includes a
number of "subcommands," which are described by printing the help message:

.. code-block:: console

   $ gmrecords -h
   usage: gmrecords [-h] [-d | -q] [-v] <command> <aliases> ...

   gmrecords is a program for retrieving and processing ground motion records, as well as exporting
   commonly used station and waveform parameters for earthquake hazard analysis.

   optional arguments:
   -h, --help            show this help message and exit
   -d, --debug           Print all informational messages.
   -q, --quiet           Print only errors.
   -v, --version         Print program version.

   Subcommands:
   <command> (<aliases>)
      assemble            Assemble raw data and organize it into an ASDF file.
      compute_station_metrics (sm)
                          Compute station metrics.
      compute_waveform_metrics (wm)
                          Compute waveform metrics.
      download            Download data and organize it in the project data directory.
      export_failure_tables (ftables)
                          Export failure tables.
      export_metric_tables (mtables)
                          Export metric tables.
      export_provenance_tables (ptables)
                          Export provenance tables.
      export_shakemap (shakemap)
                          Export files for ShakeMap input.
      generate_regression_plot (regression)
                          Generate multi-event "regression" plot.
      generate_report (report)
                          Generate summary report (latex required).
      init                Initialize the current directory as a gmprocess project directory.
      process_waveforms (process)
                           Process waveform data.
      projects (proj)     Manage gmrecords projects.

Note that some of the subcommands with longer names have short aliases to make
the command line calls more concise.

The project data directory


Project configuration
---------------------

For this tutorial, we will create a system-level project. The example in the
`Quick Start <https://github.com/usgs/groundmotion-processing/wiki/>`_ guide
uses a directory project.

.. code-block:: console

   $ gmrecords projects -c
   No project config file detected.
   Please select a project setup option:
   (1) Initialize the current directory as a gmrecords
       project, which will contain data and conf
       subdirectories.
   (2) Setup a project with data and conf locations that
       are independent of the current directory.
   > 2
   Please enter a project title: default
   You will be prompted to supply two directories for this project:
   - A *config* path, which will store the gmprocess config files.
   - A *data* path, under which will be created directories for each
     event processed.
   Please enter the conf path: [/Users/mrmanager/gmprocess_projects/default/conf]
   Please enter the data path: [/Users/mrmanager/gmprocess_projects/default/data]

   Created project: Project: default
        Conf Path: /Users/mrmanager/gmprocess_projects/default/conf
        Data Path: /Users/mrmanager/gmprocess_projects/default/data
   Please enter your name and email. This informaitn will be added
   to the config file and reported in the provenance of the data
   processed in this project.
        Name: Mr Manager
        Email: mrmanager@gmprocess.org

At this point the data and config directories are created but empty.

Download data
-------------

To limit the number of stations in this example, please edit the ``config.yml``
file (locaed in the project conf path) to restrict the search radius:

.. code-block:: yaml

   FDSNFetcher:
     radius: 0.1

Now we will download data by specifying an event id. 

.. tip::

   The easiest way to get data for events is by specifying USGS event ids. 
   These event IDs can be found by searching for events on the 
   `Search Earthquake Catalog <https://earthquake.usgs.gov/earthquakes/search/>`_
   page at the USGS. With ``gmrecords``, you can specify a single event ID or a 
   list of event IDs in a text file. Also, you can run customized searches of
   the earthquake catalog in python with 
   `libcomcat <https://github.com/usgs/libcomcat>`_.
   

We will search for records from the 2014 South Napa Earthquake 
(event ID 
`nc72282711 <https://earthquake.usgs.gov/earthquakes/eventpage/nc72282711/executive>`_).
Note that we have clipped out a bunch of terminal messages regarding the fetcher
connections because those are not important for this tutorial. 

.. code-block:: console

   $ gmrecords download -e nc72282711
   INFO 2021-01-10 17:18:48 | gmrecords.__init__: Logging level includes INFO.
   --------------------------------------------------------------------------------
   Project: default
      Conf Path: /Users/mrmanager/gmprocess_projects/default/conf
      Data Path: /Users/mrmanager/gmprocess_projects/default/data
   --------------------------------------------------------------------------------
   INFO 2021-01-10 17:18:48 | download.main: Running subcommand 'download'
   INFO 2021-01-10 17:18:49 | download.main: Number of events to download: 1
   INFO 2021-01-10 17:18:49 | download.main: Starting event: nc72282711
   ...
   INFO 2021-01-10 17:20:07 | mass_downloader.download: Downloaded 0.7 MB in total.
   4 StationStreams(s) in StreamCollection:
   3 StationTrace(s) in StationStream (passed):
      NC.N016.01.HNN | 2014-08-24T10:24:08.345000Z - 2014-08-24T10:25:41.740000Z | 200.0 Hz, 18680 samples (passed)
      NC.N016.01.HNZ | 2014-08-24T10:24:08.345000Z - 2014-08-24T10:25:41.740000Z | 200.0 Hz, 18680 samples (passed)
      NC.N016.01.HNE | 2014-08-24T10:24:08.345000Z - 2014-08-24T10:25:41.740000Z | 200.0 Hz, 18680 samples (passed)
   3 StationTrace(s) in StationStream (passed):
      YK.KRE.01.ENE | 2014-08-24T10:20:41.541000Z - 2014-08-24T10:22:38.796000Z | 200.0 Hz, 23452 samples (passed)
      YK.KRE.01.ENZ | 2014-08-24T10:20:41.541000Z - 2014-08-24T10:22:38.796000Z | 200.0 Hz, 23452 samples (passed)
      YK.KRE.01.ENN | 2014-08-24T10:20:41.541000Z - 2014-08-24T10:22:38.796000Z | 200.0 Hz, 23452 samples (passed)
   3 StationTrace(s) in StationStream (passed):
      NC.NHC..HNE | 2014-08-24T10:20:14.070000Z - 2014-08-24T10:27:44.060000Z | 100.0 Hz, 45000 samples (passed)
      NC.NHC..HNZ | 2014-08-24T10:20:14.070000Z - 2014-08-24T10:27:44.060000Z | 100.0 Hz, 45000 samples (passed)
      NC.NHC..HNN | 2014-08-24T10:20:14.070000Z - 2014-08-24T10:27:44.060000Z | 100.0 Hz, 45000 samples (passed)
   3 StationTrace(s) in StationStream (passed):
      CE.68150..HNE | 2014-08-24T10:20:21.000000Z - 2014-08-24T10:22:19.995000Z | 200.0 Hz, 23800 samples (passed)
      CE.68150..HNN | 2014-08-24T10:20:21.000000Z - 2014-08-24T10:22:19.995000Z | 200.0 Hz, 23800 samples (passed)
      CE.68150..HNZ | 2014-08-24T10:20:21.000000Z - 2014-08-24T10:22:19.995000Z | 200.0 Hz, 23800 samples (passed)

Note that the message indiates that data for 4 stations was found. The
downloaded data can be seen in the project data directory

.. code-block:: console

   $ tree .
   .
   └── nc72282711
      ├── event.json
      └── raw
         ├── CE.68150..HNE__20140824T102014Z__20140824T102744Z.mseed
         ├── CE.68150..HNN__20140824T102014Z__20140824T102744Z.mseed
         ├── CE.68150..HNZ__20140824T102014Z__20140824T102744Z.mseed
         ├── CE.68150.HN.png
         ├── CE.68150.xml
         ├── NC.N016.01.HNE__20140824T102014Z__20140824T102744Z.mseed
         ├── NC.N016.01.HNN__20140824T102014Z__20140824T102744Z.mseed
         ├── NC.N016.01.HNZ__20140824T102014Z__20140824T102744Z.mseed
         ├── NC.N016.HN.png
         ├── NC.N016.xml
         ├── NC.NHC..HNE__20140824T102014Z__20140824T102744Z.mseed
         ├── NC.NHC..HNN__20140824T102014Z__20140824T102744Z.mseed
         ├── NC.NHC..HNZ__20140824T102014Z__20140824T102744Z.mseed
         ├── NC.NHC.HN.png
         ├── NC.NHC.xml
         ├── YK.KRE.01.ENE__20140824T102014Z__20140824T102744Z.mseed
         ├── YK.KRE.01.ENN__20140824T102014Z__20140824T102744Z.mseed
         ├── YK.KRE.01.ENZ__20140824T102014Z__20140824T102744Z.mseed
         ├── YK.KRE.EN.png
         └── YK.KRE.xml

From the directory tree above, you can see how ``gmrecords`` organizes the data
directory:

- within the root data directory there are subdirectories for each event named
  by the event ID, 
- within each event directory there is 

  - an ``event.json`` file that stores event information that were retrienved 
    from the USGS data,
  - a ``raw`` directory that holds the downlaoded raw data. In this case, that
    consists of miniseed and StationXML files, 
  - PNG files that are plots of the raw data.

Assemble data
-------------

The ``assemble`` subcommand collects the data in the raw directory and 
organizes it into an ASDF file. While we can specify the event ID, if we
do not then all of the events in the data directory will be assembled.

.. code-block:: console

   $ gmrecords assemble
   INFO 2021-01-10 17:57:06 | gmrecords.__init__: Logging level includes INFO.
   --------------------------------------------------------------------------------
   Project: default
      Conf Path: /Users/mrmanager/gmprocess_projects/default/conf
      Data Path: /Users/mrmanager/gmprocess_projects/default/data
   --------------------------------------------------------------------------------
   INFO 2021-01-10 17:57:06 | assemble.main: Running subcommand 'assemble'
   [nc72282711 2014-08-24T10:20:44.070000Z 38.215 -122.312 11.1km M6.0 mw]
   INFO 2021-01-10 17:57:06 | assemble.main: Number of events to assemble: 1
   INFO 2021-01-10 17:57:06 | assemble.main: Starting event: nc72282711
   4 StationStreams(s) in StreamCollection:
   3 StationTrace(s) in StationStream (passed):
      NC.N016.01.HNN | 2014-08-24T10:24:08.345000Z - 2014-08-24T10:25:41.740000Z | 200.0 Hz, 18680 samples (passed)
      NC.N016.01.HNZ | 2014-08-24T10:24:08.345000Z - 2014-08-24T10:25:41.740000Z | 200.0 Hz, 18680 samples (passed)
      NC.N016.01.HNE | 2014-08-24T10:24:08.345000Z - 2014-08-24T10:25:41.740000Z | 200.0 Hz, 18680 samples (passed)
   3 StationTrace(s) in StationStream (passed):
      YK.KRE.01.ENE | 2014-08-24T10:20:41.541000Z - 2014-08-24T10:22:38.796000Z | 200.0 Hz, 23452 samples (passed)
      YK.KRE.01.ENZ | 2014-08-24T10:20:41.541000Z - 2014-08-24T10:22:38.796000Z | 200.0 Hz, 23452 samples (passed)
      YK.KRE.01.ENN | 2014-08-24T10:20:41.541000Z - 2014-08-24T10:22:38.796000Z | 200.0 Hz, 23452 samples (passed)
   3 StationTrace(s) in StationStream (passed):
      NC.NHC..HNE | 2014-08-24T10:20:14.070000Z - 2014-08-24T10:27:44.060000Z | 100.0 Hz, 45000 samples (passed)
      NC.NHC..HNZ | 2014-08-24T10:20:14.070000Z - 2014-08-24T10:27:44.060000Z | 100.0 Hz, 45000 samples (passed)
      NC.NHC..HNN | 2014-08-24T10:20:14.070000Z - 2014-08-24T10:27:44.060000Z | 100.0 Hz, 45000 samples (passed)
   3 StationTrace(s) in StationStream (passed):
      CE.68150..HNE | 2014-08-24T10:20:21.000000Z - 2014-08-24T10:22:19.995000Z | 200.0 Hz, 23800 samples (passed)
      CE.68150..HNN | 2014-08-24T10:20:21.000000Z - 2014-08-24T10:22:19.995000Z | 200.0 Hz, 23800 samples (passed)
      CE.68150..HNZ | 2014-08-24T10:20:21.000000Z - 2014-08-24T10:22:19.995000Z | 200.0 Hz, 23800 samples (passed)

   INFO 2021-01-10 17:57:08 | stream_workspace.addStreams: Adding waveforms for station N016
   INFO 2021-01-10 17:57:08 | stream_workspace.addStreams: Adding waveforms for station KRE
   INFO 2021-01-10 17:57:08 | stream_workspace.addStreams: Adding waveforms for station NHC
   INFO 2021-01-10 17:57:08 | stream_workspace.addStreams: Adding waveforms for station 68150

   The following files have been created:
   File type: Workspace
      /Users/mrmanager/gmprocess_projects/default/data/nc72282711/workspace.h5

The console message indicates that the ``workspace.h5`` ASDF file has been
created. 

.. note::

   The `Seismic Data <https://seismic-data.org/>`_ folks have developed a
   graphical user interface to explore ASDF data sets called
   `ASDF Sextant <https://github.com/SeismicData/asdf_sextant>`_
   and this may be useful for browsing the contents of the ASDF file.
   Since ASDF is an HDF5 specification, it can also be loaded in most 
   programming languages using
   `HDF5 <https://www.hdfgroup.org/solutions/hdf5/>`_ libraries.


Process Waveforms
-----------------------
The ``process_waveforms`` (or just ``process`` for short) subcommand reads in
the raw data from the ASDF workspace files that were created by the assemble
subcommand, and then applies the waveform processing steps that are specified 
the config file (in the processing section). The processed waveforms are then 
added to the ASDF workspace file.

.. code-block:: console

   $ gmrecords process
   INFO 2021-01-10 18:16:22 | gmrecords.__init__: Logging level includes INFO.
   --------------------------------------------------------------------------------
   Project: default
      Conf Path: /Users/mrmanager/gmprocess_projects/default/conf
      Data Path: /Users/mrmanager/gmprocess_projects/default/data
   --------------------------------------------------------------------------------
   INFO 2021-01-10 18:16:22 | process_waveforms.main: Running subcommand 'process_waveforms'
   INFO 2021-01-10 18:16:22 | process_waveforms.main: Processing tag: 20210111011622
   INFO 2021-01-10 18:16:22 | process_waveforms.main: Processing 'unprocessed' streams for event nc72282711...
   WARNING 2021-01-10 18:16:22 | phase.calc_snr: Noise window for NC.N016.01.HNE has mean of zero.
   WARNING 2021-01-10 18:16:22 | phase.calc_snr: Noise window for NC.N016.01.HNN has mean of zero.
   WARNING 2021-01-10 18:16:22 | phase.calc_snr: Noise window for NC.N016.01.HNZ has mean of zero.
   INFO 2021-01-10 18:16:23 | processing.process_streams: Stream: CE.68150.HN
   INFO 2021-01-10 18:16:23 | processing.process_streams: Stream: NC.N016.HN
   INFO 2021-01-10 18:16:23 | stationtrace.fail: snr_check
   INFO 2021-01-10 18:16:23 | stationtrace.fail: Failed SNR check; SNR less than threshold.
   INFO 2021-01-10 18:16:23 | stationtrace.fail: snr_check
   INFO 2021-01-10 18:16:23 | stationtrace.fail: Failed SNR check; SNR less than threshold.
   INFO 2021-01-10 18:16:24 | stationtrace.fail: snr_check
   INFO 2021-01-10 18:16:24 | stationtrace.fail: Failed SNR check; SNR less than threshold.
   INFO 2021-01-10 18:16:24 | processing.process_streams: Stream: NC.NHC.HN
   INFO 2021-01-10 18:16:24 | processing.process_streams: Stream: YK.KRE.EN
   INFO 2021-01-10 18:16:24 | processing.process_streams: Finished processing streams.
   INFO 2021-01-10 18:16:25 | stream_workspace.addStreams: Adding waveforms for station 68150
   INFO 2021-01-10 18:16:25 | stream_workspace.addStreams: Adding waveforms for station N016
   INFO 2021-01-10 18:16:25 | stream_workspace.addStreams: Adding waveforms for station NHC
   INFO 2021-01-10 18:16:25 | stream_workspace.addStreams: Adding waveforms for station KRE
   No new files created.

Note that the console messages indicate that some of the tracles failed the 
signal-to-noise requirements.

Generate Report
---------------

For each evennt, the ``gmrecords`` command can generate a "report" that is
useful to review which streams failed and why. The report gives a 1-page per 
station summary that includes:

- the acceleration and velocity plots,
- the location where the signal and noise windows were split,
- the signal and noise spectra (raw and smoothed), and
- a table of the processing steps applied to the record.

.. code-block:: console

   $ gmrecords report
   INFO 2021-01-10 18:25:51 | gmrecords.__init__: Logging level includes INFO.
   --------------------------------------------------------------------------------
   Project: default
      Conf Path: /Users/mrmanager/gmprocess_projects/default/conf
      Data Path: /Users/mrmanager/gmprocess_projects/default/data
   --------------------------------------------------------------------------------
   INFO 2021-01-10 18:25:51 | generate_report.main: Running subcommand 'generate_report'
   INFO 2021-01-10 18:25:52 | generate_report.main: Creating diagnostic plots for event nc72282711...
   INFO 2021-01-10 18:26:06 | generate_report.main: Generating summary report for event nc72282711...

   The following files have been created:
   File type: Station map
      /Users/mrmanager/gmprocess_projects/default/data/nc72282711/stations_map.png
   File type: Moveout plot
      /Users/mrmanager/gmprocess_projects/default/data/nc72282711/moveout_plot.png
   File type: Summary report
      /Users/mrmanager/gmprocess_projects/default/data/nc72282711/report_nc72282711.pdf


From the report (see below), you can see that the NC.N016 station failed the 
SNR check. You can also see that it is likely because the signal and noise 
windows were not cleanly separated and so if the windowing were adjusted this 
record would likely pass the signal-to-noise requirement.

.. tab:: NC.NHC

    .. image:: ../../_static/nc72282711_NC.NHC.HN.png

.. tab:: NC.N016

    .. image:: ../../_static/nc72282711_NC.N016.HN.png

.. tab:: CE.68150

    .. image:: ../../_static/nc72282711_CE.68150.HN.png

.. tab:: YK.KRE

    .. image:: ../../_static/nc72282711_YK.KRE.EN.png


Compute Station Metrics
-----------------------

The ``compute_station_metrics`` subcommand computes station metrics (like
epicentral distance) and add them to the ASDF workspace file.

.. code-block:: console

   $ gmrecords compute_station_metrics
   INFO 2021-01-10 19:23:43 | gmrecords.__init__: Logging level includes INFO.
   --------------------------------------------------------------------------------
   Project: default
      Conf Path: /Users/mrmanager/gmprocess_projects/default/conf
      Data Path: /Users/mrmanager/gmprocess_projects/default/data
   --------------------------------------------------------------------------------
   INFO 2021-01-10 19:23:43 | compute_station_metrics.main: Running subcommand 'compute_station_metrics'
   INFO 2021-01-10 19:23:43 | compute_station_metrics.main: Computing station metrics for event nc72282711...
   INFO 2021-01-10 19:23:44 | compute_station_metrics.main: Calculating station metrics for CE.68150.HN...
   INFO 2021-01-10 19:23:48 | compute_station_metrics.main: Calculating station metrics for NC.N016.HN...
   INFO 2021-01-10 19:23:51 | compute_station_metrics.main: Calculating station metrics for NC.NHC.HN...
   INFO 2021-01-10 19:23:55 | compute_station_metrics.main: Calculating station metrics for YK.KRE.EN...
   INFO 2021-01-10 19:23:59 | compute_station_metrics.main: Added station metrics to workspace files with tag '20210111011622'.
   No new files created.

Compute Waveform Metrics
-----------------------

The ``compute_waveform_metrics`` subcommand computes waveform metrics (such as 
spectral accelerations) and are added to the ASDF workspace file. The waveform 
metrics that are computed are defined in the metrics section of the conf file. 
The metrics are defined by intensity metric types (e.g., spectral acceleration 
vs duration) and intensity measure component (how the instrument components are 
combined).

.. code-block:: console 

   $ gmrecords compute_waveform_metrics
   INFO 2021-01-10 19:25:57 | gmrecords.__init__: Logging level includes INFO.
   --------------------------------------------------------------------------------
   Project: default
      Conf Path: /Users/mrmanager/gmprocess_projects/default/conf
      Data Path: /Users/mrmanager/gmprocess_projects/default/data
   --------------------------------------------------------------------------------
   INFO 2021-01-10 19:25:57 | compute_waveform_metrics.main: Running subcommand 'compute_waveform_metrics'
   INFO 2021-01-10 19:25:57 | compute_waveform_metrics.main: Computing waveform metrics for event nc72282711...
   INFO 2021-01-10 19:25:58 | compute_waveform_metrics.main: Calculating waveform metrics for CE.68150.HN...
   INFO 2021-01-10 19:26:03 | compute_waveform_metrics.main: Calculating waveform metrics for NC.NHC.HN...
   INFO 2021-01-10 19:26:08 | compute_waveform_metrics.main: Calculating waveform metrics for YK.KRE.EN...
   INFO 2021-01-10 19:26:14 | compute_waveform_metrics.main: Added waveform metrics to workspace files with tag '20210111011622'.
   No new files created.

Note that you can see from the console output that the waveform metrics were 
not computed for the station that failed the signal-to-noise ratio test.



.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
