# Data Structures

gmprocess uses a number of data structures that make reading and processing
significant motion data easier.


## StationTrace

Obspy provides a Trace object that serves as a container for waveform data from
a single channel, as well as some basic metadata about the waveform start/end
times, number of points, sampling rate/interval, and
network/station/channel/location information.

The StationTrace object builds on this metadata, adding to it the following
features:

 - Validation that length of data matches the number of points in the metadata.
 - Validation that required values are set in metadata (see standard below).
 - fail() method which can be used by processing routines to mark when
   processing of the StationTrace has failed some sort of check (signal to
   noise ratio, etc.)
 - free_field property which can be used to query the object to ensure that its
   data comes from a free-field sensor (i.e., not attached to a structure).
   Note: this is not always known.
 - Tracking of processing steps that have been performed - these are aligned
   with the  SEIS-PROV standard for processing provenance, described here:
   http://seismicdata.github.io/SEIS-PROV/_generated_details.html#activities
 - Tracking of arbitrary metadata in the form of a parameters dictionary.
 - In addition to the usual Trace metadata, StationTrace a `coordinates`
   dictionary containing latitude, longitude, and elevation of the station, a
   `format_specific` dictionary containing information found in the more
   esoteric formats defined by the engineering community. Finally, StationTrace
   contains the `standard` dictionary, described by the following table:

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
Trace objects. gmprocess builds on this object to contain StationTrace objects,
and provides facilities for extracting Obspy inventory data structures, and 
provenance from the contained StationTrace objects.

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