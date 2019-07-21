# StreamCollection

The ObsPy data structures do not provide any mechanism for logical grouping of
waveforms from various sensors. The StreamCollection class provides this
functionality and thus saves the user from figuring out which traces should go
together.

## Example Usage

```python
import glob
from gmprocess.io.read import read_data
from gmprocess.streamcollection import StreamCollection

# these sample files can be found in the repository
# under gmprocess/data/testdata/knet/us2000cnnl
# knet files are stored one channel per file.
datafiles = glob.glob('AOM*')
streams = []
for datafile in datafiles:
  streams += read_data(datafile)

print(len(streams)) # should be 27
collection = StreamCollection(streams)
print(len(collection)) # should be 9 streams grouped by station

# For information
collection.describe()
```
