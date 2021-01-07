# StationStream

ObsPy provides a Stream object that serves as a container for zero-to-many
Trace objects, and gmprocess subclasses the Stream object with the StationStream
object, which contains StationTrace objects. It also provides facilities for
extracting Obspy inventory data structures, and provenance from the contained
StationTrace objects.


The StationStream class is meant for grouping Traces from the same "station".
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


## Example Usage

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
