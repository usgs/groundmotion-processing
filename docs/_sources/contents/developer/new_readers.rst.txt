Adding New Data Readers
=======================

Most of the difficulty in writing data file readers for the various formats
supported by *gmprocess* comes in handling the various types of headers and
inconsistencies in adherence to the various standards. Here we'll be removing
those from the equation and presenting a semi-idealized data format and some
code to read it.

**The Format**

.. code-block:: text

   Source: Complete Strong Motion Network
   Network: CS
   Station: ABCD
   Station Latitude: 32.443343
   Station Longitude: -127.753918
   Station Elevation (m): 10.0
   Instrument: Acme Strong Motion Sensor
   Serial Number: 123456
   Units: cm/s^2
   Structure Type: Free field sensor
   Channel 1 Horizontal Orientation: 0
   Channel 2 Horizontal Orientation: 90
   Channel 3 Horizontal Orientation: 0
   Vertical Channel: 3
   Samples: 10
   Record Start Time: 2019-05-01 12:34:56.010
   Sampling Rate (Hz): 100
      0.001     0.011     0.021
      0.002     0.012     0.022
      0.003     0.013     0.023
      0.004     0.014     0.024
      0.005     0.015     0.025
      0.006     0.016     0.026
      0.007     0.017     0.027
      0.008     0.018     0.028
      0.009     0.019     0.029
      0.010     0.020     0.030


**The Code**

The sample module below has been tested with the above data, and can be used as
a template for writing a data reader for a new format. This data format is (as
it's name implies) complete in terms of the information required to construct a
``StationStream`` object. Real-world formats may not be as complete. The bare 
minimum information needed to construct a ``StationStream`` of minimal use 
includes:

- Station code
- Station horizontal coordinates
- Some indication of the input units
- Sampling rate or sampling interval
- Distinction between horizontal and vertical channels
- Either a channel orientation (0-360) or some indication of what is E-W and N-S

Record start time is **strongly** desired, but a "NaN" record start time value 
of 1970-01-01 00:00:00 will be inserted by ObsPy if not supplied.

The code below contains comments that should be useful as guides when writing
your own reader. A finished reader with tests and data should be organized as 
below.

Assumptions: The event ID associated with this record is **csabcd1234**.

- gmprocess->io->complete->core.py (the code below)
- tests->gmprocess->io->complete->complete_test.py (test code for core.py)
- gmprocess->data->testdata->complete->csabcd1234->complete.dat (at least one 
  example of the file format)
- gmprocess->data->testdata->complete->event.json->event.json (JSON file 
  containing basic event information):

.. code-block:: json

   {
      "id": "csabcd1234",
      "time": "2019-05-01T12:34:55.010",
      "lat": 32.443,
      "lon": -127.753,
      "depth": 20.0,
      "magnitude": 6.0
   }


.. code-block:: python

   #!/usr/bin/env python

   # stlib imports
   import os.path

   # third party imports
   import numpy as np
   from obspy.core.utcdatetime import UTCDateTime

   # local imports
   from gmprocess.core.stationtrace import StationTrace
   from gmprocess.core.stationstream import StationStream
   from gmprocess.io.seedname import get_channel_name, is_channel_north

   TEXT_HDR_ROWS = 17
   SOURCE_TYPE = 'Complete Strong Motion Network'


   def is_complete(filename):
       '''Determine whether input file is from the Complete Strong Motion Network.

       Args:
           filename (str):
               Input candidate Complete format file.
       Returns:
           bool:
               True if input file matches the Complete format, False otherwise.
       '''
       try:
           with open(filename, 'rt') as f:
               lines = [next(f) for x in range(TEXT_HDR_ROWS)]
           if lines[0].split(':')[1].strip() == SOURCE_TYPE:
               return True
           return False
       except Exception:
           return False


   def read_complete(filename):
       '''Read file in the Complete file format, return a list of one StationStream.

       Args:
           filename (str):
               Input candidate Complete format file.
       Returns:
           list: Sequence of one StationStream object.
       '''
       # it is probably a good idea to separate the reading of the
       # header information from the reading of the data
       header = _read_header(filename)
       stats = _get_stats(header)

       # Reading FORTRAN formatted fixed-width column data is simple
       # thanks to the numpy genfromtxt() method.
       # if the data is in units other than gals (c/s^2), perform
       # the appropriate conversion here.
       data = np.genfromtxt(filename, skip_header=TEXT_HDR_ROWS)

       # We subclassed the Obspy Trace object to carry around
       # more metadata and also perform some validation.
       # Here we construct three traces from each of the
       # three columns of data and the relevant header info
       trace1 = _get_channel_trace(1, header, stats, data)
       trace2 = _get_channel_trace(2, header, stats, data)
       trace3 = _get_channel_trace(1, header, stats, data)

       # We have also subclassed the Obspy Stream object
       stream = StationStream(traces=[trace1, trace2, trace3])

       # All readers should return a list of StationStream objects, since
       # some formats contain records from multiple stations in one file.
       return [stream]


   def _read_header(filename):
       # read in the text header lines, turn them into a dictionary.
       header = {}
       with open(filename, 'rt') as f:
           lines_read = 0
           while lines_read < TEXT_HDR_ROWS:
               line = f.readline()
               parts = line.split(':')
               header[parts[0].strip()] = parts[1].strip()

      return header


   def _get_stats(header):
       # fill in the Obspy stats dictionary with the data described here:
       # https://docs.obspy.org/packages/autogen/obspy.core.trace.Stats.html
       # Also add two sub-dictionaries, "standard" and "coordinates".
       # "standard" is meant to hold metadata we discovered to be common
       # among many formats. "coordinates" is meant to hold latitude,
       # longitude, and elevation of the station. In Obspy, this type of
       # information is commonly kept in the Inventory object:
       #  https://docs.obspy.org/packages/autogen/obspy.core.inventory.inventory.Inventory.html
       stats = {}
       stats['starttime'] = UTCDateTime(header['Record Start Time'])
       stats['sampling_rate'] = float(header['Sampling Rate (Hz)'])
       stats['npts'] = int(header['Samples'])
       stats['station'] = header['Station']
       stats['network'] = header['Network']

       standard = {}
       standard['source'] = header['Source']
       standard['instrument'] = header['Instrument']
       standard['sensor_serial_number'] = header['Serial Number']
       head, tail = os.path.split(filename)
       standard['source_file'] = tail or os.path.basename(head)
       standard['process_level'] = 'uncorrected physical units'
       standard['units'] = 'acc'
       standard['source_format'] = 'complete'
       standard['instrument_damping'] = np.nan
       standard['structure_type'] = ''
       standard['comments'] = ''
       standard['corner_frequency'] = np.nan
       standard['instrument_period'] = np.nan
       standard['station_name'] = ''
       standard['process_time'] = ''

       coordinates = {}
       coordinates['latitude'] = header['Station Latitude']
       coordinates['longitude'] = header['Station Longitude']
       coordinates['elevation'] = header['Station Elevation (m)']

       stats['standard'] = standard.copy()
       stats['coordinates'] = coordinates.copy()

       return stats


   def _get_channel_trace(channel_number, header,
                          stats, data):
       # Create a StationTrace object from the given channel number
       # and input metadata and data.
       channel_stats = stats.copy()
       orientation = float(
           header['Channel %i Horizontal Orientation' % channel_number])
       channel_stats['standard']['horizontal_orientation'] = orientation
       is_vertical = header['Vertical Channel'] == channel_number
       is_north = is_channel_north(orientation)
       channel_stats['channel'] = get_channel_name(
           stats['sampling_rate'],
           is_acceleration=True,
           is_vertical=is_vertical,
           is_north=is_north
       )
       channelidx = channel_number - 1
       trace = StationTrace(data=data[:, channelidx], header=channel_stats)
       return trace


.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
