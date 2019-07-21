# Waveform metrics

Here we expand the prior example to demonstrate how to compute waveform
metrics.

```python
import os
import pkg_resources

from gmprocess.streamcollection import StreamCollection
from gmprocess.config import get_config
from gmprocess.processing import process_streams
from gmprocess.event import get_event_object
from gmprocess.metrics.station_summary import StationSummary

# Path to example data
datapath = os.path.join('data', 'testdata', 'demo', 'ci38457511', 'raw')
datadir = pkg_resources.resource_filename('gmprocess', datapath)
sc = StreamCollection.from_directory(datadir)

# Includes 3 StationStreams, each with 3 StationTraces
sc.describe()

# Get the default config file
conf = get_config()

# Get event object
event = get_event_object('ci38457511')

# Process the straems
psc = process_streams(sc, event, conf)
psc.describe()

# Define the IMCs and IMTs we want
imcs = ['rotd50']
imts = ['PGA', 'sa1.0']

# Get the StationSummary for the first StationStream
stream_summary = StationSummary.from_stream(
    psc[0], imcs, imts, event)
print(stream_summary.pgms)
#          IMT         IMC     Result
# 0  SA(1.000)  ROTD(50.0)  17.821136
# 0        PGA  ROTD(50.0)  40.702096
```
