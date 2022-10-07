---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: '0.8'
    jupytext_version: '1.4.1'
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Data Structures


## StationTrace

ObsPy provides a `Trace` object that serves as a container for waveform data 
from a single channel, as well as some basic metadata about the waveform 
start/end times, number of points, sampling rate/interval, and
network/station/channel/location information.

`gmprocess` subclasses the `Trace` object with a `StationTrace` object, 
which provides the following additional features:

- Validation that length of data matches the number of points in the metadata.
- Validation that required values are set in metadata.
- A `fail` method which can be used by processing routines to mark when
  processing of the `StationTrace` has failed some sort of check (signal to
  noise ratio, etc.)
- A `free_field` property which can be used to query the object to ensure that
  its data comes from a free-field sensor. 

  ```{note}

     The free field condition is not always known reliably, and different people
     have have different definitions of the term `free_field`. When possible,
     we define a mapping between location code and the `free_field` property.
     For example, see the `LOCATION_CODES` variable `core.py` in 
     `gmprocess.io.fdsn`.
  ```

- Methods (e.g., `getProvenance`, `setProvenance`) for tracking  processing
  steps that have been performed. These are aligned with the 
  [SEIS-PROV ](http://seismicdata.github.io/SEIS-PROV/_generated_details.html#activities)
  standard for processing provenance.
- Methods (e.g., `getParameter` and `setParameter`) for tracking of
  arbitrary metadata in the form of a dictionary as trace property 
  (`self.parameters`).

- In addition to the usual `Trace` metadata, `StationTrace` has

  - a `coordinates` dictionary containing latitude, longitude, and elevation
    of the station,

  - a `format_specific` dictionary containing information found in some file
    formats but cannot be expected across all formats, and

  - a `standard` dictionary, metadata that we expect to find in all formats.


## StationStream

ObsPy provides a `Stream` object that serves as a container for zero-to-many
`Trace` objects, and gmprocess subclasses the `Stream` object with the 
`StationStream` object, which contains `StationTrace` objects. It also 
provides facilities for extracting Obspy inventory data structures, and 
provenance from the contained `StationTrace` objects.

The `StationStream` class is meant for grouping `Traces` from the same 
"station". In practice, what this really means is usually all of the channels 
from one instrument, with the same start and end times. Thus, the 
`StationStream` object has a `get_id` method, which returns a string that 
consists of the network code, station code, and the first two characters of the
channel code, since these should all be applicable to all traces in the 
`StationStream` object.

`StationStream` checks that all of the `StationTraces` have the same ID, 
sample rates, number of points, and start times.

`StationStream` also has a `passed` attribute. This is useful for tracking 
data that has not passed checks. In most of these cases, we do not want halt
the execution of the processing code by raising an exception, but we do need
to know that a problem occurred.


### Example Usage

This example below demonstrates reading data from the Taiwanese CWB
data format, and saving it into a MiniSEED file accompanied by a
StationXML file, suitable for passing to other packages.

```{code-cell} ipython3
:tags: [remove-stderr]
from pathlib import Path
from gmprocess.io.read import read_data

datadir = Path("..") / ".." / ".." / "tests" / "data" / "cwb" / "us1000chhc"
# cwb files are stored as three channels per file.
datafile = datadir / "1-EAS.dat"
stream = read_data(datafile)[0]
inventory = stream.getInventory()

stream.write("example.mseed", format="MSEED")
inventory.write("example.xml", format="STATIONXML")
```

## StreamCollection

The ObsPy data structures do not provide any mechanism for logical grouping of
waveforms from various sensors. The `StreamCollection` class provides this
functionality and thus saves the user from figuring out which traces should go
together.

### Example Usage

Imports:

```{code-cell} ipython3
from pathlib import Path
from gmprocess.io.read import read_data
from gmprocess.core.streamcollection import StreamCollection
```

Then read in some example test data that is distributed with gmprocess:

```{code-cell} ipython3
datadir = Path("..") / ".." / ".." / "tests" / "data" / "knet" / "us2000cnnl"
datafiles = datadir.glob("AOM*")

streams = []
for datafile in datafiles:
    streams += read_data(datafile)

print(len(streams)) 
```

There should be 27 individual streams because each channel is handled as a 
separate stream. 

Now create a StreamCollection and it will group the channels by instrument.

```{code-cell} ipython3
collection = StreamCollection(streams)
print(len(collection)) 
```

So the length of the collection should be 9.

The `describe` method gives additional information.

```{code-cell} ipython3
collection.describe()
```



% Indices and tables

% ==================

% * :ref:`genindex`

% * :ref:`modindex`

% * :ref:`search`
