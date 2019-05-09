# Data Structures

gmprocess uses a number of data structures that make reading and processing
significant motion data easier.


## StationTrace

Obspy provides a Trace object that serves as a container for waveform data from
a single channel, as well as some basic metadata about the waveform start/end
times, number of points, sampling rate/interval, and
network/station/channel/location information.

gmprocess subclasses the Trace object with a StationTrace object, which provides
the following additional features:

 - Validation that length of data matches the number of points in the metadata.
 - Validation that required values are set in metadata (see standard below).
 - A `fail` method which can be used by processing routines to mark when
   processing of the StationTrace has failed some sort of check (signal to
   noise ratio, etc.)
 - A `free_field` property which can be used to query the object to ensure that
   its data comes from a free-field sensor. Note: this is not always known
   reliably, and different people have have different definitions of the term
   `free_field`. When possible, we define a mapping between location code
   and the `free_field` property. For example, see the `LOCATION_CODES`
   variable `core.py` in `gmprocess.io.fdsn`.
 - Methods (e.g., `getProvenance`, `setProvenance`) for tracking  processing
   steps that have been performed. These are aligned with the SEIS-PROV
   standard for processing provenance, described here:
   http://seismicdata.github.io/SEIS-PROV/_generated_details.html#activities
 - Methods (e.g., `getParameter` and `setParameter`) for tracking of arbitrary
   metadata in the form of a dictionary as trace property (`self.parameters`).
 - In addition to the usual Trace metadata, StationTrace has
   - a `coordinates` dictionary containing latitude, longitude, and elevation
     of the station,
   - a `format_specific` dictionary containing information found in some file
     formats but cannot be expected across all formats, and
   - a `standard` dictionary, metadata that we expect to find in all formats.
     More details are given in this table:


<table>
  <tr>
    <th>Key Name</th>
    <th>Description</th>
    <th>Data Type</th>
    <th>Required?</th>
    <th>Default Value</th>
  </tr>

  <tr>
    <td>source</td>
    <td>Long form network description</td>
    <td>str</td>
    <td>Yes</td>
    <td></td>
  </tr>

  <tr>
    <td>horizontal_orientation</td>
    <td>Azimuth of the channel</td>
    <td>float</td>
    <td>No</td>
    <td>NaN</td>
  </tr>

  <tr>
    <td>station_name</td>
    <td>Long form station description</td>
    <td>str</td>
    <td>No</td>
    <td></td>
  </tr>  

  <tr>
    <td>instrument_period</td>
    <td>Natural sensor period</td>
    <td>float</td>
    <td>No</td>
    <td>NaN</td>
  </tr>

  <tr>
    <td>instrument_damping</td>
    <td>Natural sensor damping</td>
    <td>float</td>
    <td>No</td>
    <td>NaN</td>
  </tr>

  <tr>
    <td>process_time</td>
    <td>Time at which the raw data was processed</td>
    <td>str</td>
    <td>No</td>
    <td></td>
  </tr>

  <tr>
    <td>process_level</td>
    <td>Description of the raw data processing level</td>
    <td>str</td>
    <td>No</td>
    <td>One of 'raw counts', 'uncorrected physical units', 'corrected physical units', 'derived time series'</td>
  </tr>

  <tr>
    <td>sensor_serial_number</td>
    <td>Sensor serial number</td>
    <td>str</td>
    <td>No</td>
    <td></td>
  </tr>
  
  <tr>
    <td>instrument</td>
    <td>Name (model, etc.) of sensor</td>
    <td>str</td>
    <td>No</td>
    <td></td>
  </tr>

  <tr>
    <td>structure_type</td>
    <td>Description of structure type to which sensor is attached</td>
    <td>str</td>
    <td>No</td>
    <td></td>
  </tr>

  <tr>
    <td>corner_frequency</td>
    <td>Natural corner frequency</td>
    <td>float</td>
    <td>No</td>
    <td>NaN</td>
  </tr>

  <tr>
    <td>units</td>
    <td>Units of raw data</td>
    <td>str</td>
    <td>Yes</td>
    <td></td>
  </tr>

  <tr>
    <td>source_format</td>
    <td>Format of raw data (see Formats).</td>
    <td>str</td>
    <td>Yes</td>
    <td></td>
  </tr>

  <tr>
    <td>comments</td>
    <td>Any free-text comments from raw data file</td>
    <td>str</td>
    <td>No</td>
    <td></td>
  </tr>

</table>

## StationStream

Obspy provides a Stream object that serves as a container for zero-to-many
Trace objects, and gmprocess subclasses the Stream object with the StationStream
object, which contains StationTrace objects. It also provides facilities for
extracting Obspy inventory data structures, and provenance from the contained
StationTrace objects.


The StationStream class is meant for grouping Traces from the same ``station''.
In practice, what this really means is usually all of the channels from one
instrument, with the same start and end times. Thus, the `StationStream `
object has a `get_id` method, which returns a string that consists of the
network code, station code, and the first two characters of hte channel code,
since these should all be applicable to all traces in the StationStream object.

StationStream checks that all of the StationTraces have the same ID, sample
rates, number of points, and start times.

StationStream also has a `passed` attribute. This is useful for tracking data
that has not passed checks. In most of these cases, we do not want halt
the execution of the processing code by raising an exception, but we do need
to know that a problem occurred.


### Usage

This example below demonstrates reading data from the Taiwanese CWB
data format, and saving it into a MiniSEED file accompanied by a 
StationXML file, suitable for passing to other packages.

```python
from gmprocess.io.read import read_data

# this sample file can be found in the repository
# under gmprocess/data/testdata/cwb/us1000chhc
# cwb files are stored as three channels per file.
datafile = '1-EAS.dat'
stream = read_data(datafile)[0]
inventory = stream.getInventory()

stream.write("example.mseed", format="MSEED")
inventory.write("example.xml", format="STATIONXML")
```

## StreamCollection

The Obspy data structures do not provide any mechanism for logical grouping of
waveforms from various sensors. The StreamCollection class provides this
functionality and thus saves the user from figuring out which traces should go
together.

### Usage

```python
import glob
from gmprocess.io.read import read_data
from gmprocess.streamcollection import StreamCollection

# these sample files can be found in the repository
# under gmprocess/data/testdata/knet/us2000cnnl
# knet files are stored one channel per file.
datafiles = glob.glob('AOM.*')
streams = []
for datafile in datafiles:
  streams += read_data(datafile)

print(len(streams)) # should be 27
collection = StreamCollection(streams)
print(len(collection)) # should be 9 streams grouped by station
```