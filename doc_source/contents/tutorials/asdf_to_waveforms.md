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
# Processed Waveforms from ASDF File

For browsing information in the 
[HDF5](https://www.hdfgroup.org/solutions/hdf5/)/[ASDF](https://asdf-definition.readthedocs.io/en/latest/)
files output by gmprocess, the overview of the organizational structure in the 
[Workspace section of the manual](../manual/workspace)
should be a useful reference. 

First, some imports

```{code-cell} ipython3
import os
import pkg_resources

from gmprocess.io.asdf.stream_workspace import StreamWorkspace
```

And now we open an example ASDF file

```{code-cell} ipython3
# Path to example data
rel_path = os.path.join(
  'data', 'testdata', 'asdf', 'nc72282711', 'workspace.h5')
data_path = pkg_resources.resource_filename('gmprocess', rel_path)
workspace = StreamWorkspace.open(data_path)
```

First, check to see what labels are present. There is typically the 
"unprocessed" label and one for the processed waveforms. The processed 
waveform label is "default" unless the user has set the label for the 
processed waveforms.

```{code-cell} ipython3
labels = workspace.getLabels()
print(labels)
```

It is generally possible to have multiple events in an ASDF file, but gmprocess
follows a convention of having one event per ASDF file. 

```{code-cell} ipython3
eventids = workspace.getEventIds()
print(eventids)
```

The ASDF data structure can be accessed directly from the workspace object via
the `dataset` attribute

```{code-cell} ipython3
ds = workspace.dataset
station_list = ds.waveforms.list()
print(station_list)
```

You can retrieve an obspy stream from the ASDF by browsing the waveforms with 
knowledge of the stations, event ID, and labels. Note that ASDF uses a tag 
that combines the event ID and label.

```{code-cell} ipython3
---
render:
  image:
    height: 350px
---
st = ds.waveforms['NP.1737']['nc72282711_default']
print(st)
st.plot();
```

If you want a StreamCollection object (see [here](../manual/data_structures) 
for more info), there is a method for constructing it from the workspace
file

```{code-cell} ipython3
sc = workspace.getStreams(
  'nc72282711', stations=['NP.1737'], labels=['default'])
sc.describe()
```

One convenient aspect of a StreamCollection is that it includes StationStream 
objects, and it is easy to access metadata, including the provenance of the 
data. 

```{code-cell} ipython3
sta_st = sc[0]
print(sta_st[0].getProvDataFrame())
```

You can also get the entire provenance document for all stations.

```{code-cell} ipython3
prov = workspace.getProvenance('nc72282711', labels=['default'])
print(prov)
```
