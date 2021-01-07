# Python scripting

Here we provide an example of how to use our code as a library to write
your own scripts. In this example, we read in some data, apply the default
processing steps, and the make plots of the processed waveforms.

```python
import os
import pkg_resources

from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.config import get_config
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.utils.event import get_event_object

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

# Save plots of processed records
for st in psc:
    st.plot(outfile='%s.png' % st.get_id())
```

