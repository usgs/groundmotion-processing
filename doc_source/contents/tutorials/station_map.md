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
# Plotting Seismograms on the Station Map

It may be useful to compare seismograms interactively on a map. Although gmprocess does not have this capability, it is relatively straightforward to do using folium for generating the map and altair for creating the figures.

Note that the altair package is needed for the interactive plotting, but is not used by gmprocess and will need to be installed separately. The package can be installed via conda or mamba:

```conda install altair```

```mamba install altair```

We first take care of the imports. 

```{code-cell} ipython3
import numpy as np
import pandas as pd
import folium
import altair as alt
import json
import os
import pkg_resources

from gmprocess.io.asdf.stream_workspace import StreamWorkspace
```

We are using a ground motion dataset of earthquakes from the 2001 Nisqually earthquake. The processed waveforms in the ASDF file will be used for this tutorial.

```{code-cell} ipython3
# Open ASDF file containing Nisqually dataset
rel_path = os.path.join(
  'data', 'testdata', 'asdf', 'uw10530748', 'workspace.h5')
data_path = pkg_resources.resource_filename('gmprocess', rel_path)
workspace = StreamWorkspace.open(data_path)
```

Lets first list the stations stored in the ASDF file

```{code-cell} ipython3
ds = workspace.dataset
station_list = ds.waveforms.list()
print(station_list)
```

As an illustration, we will plot the vertical component on a map for a few stations such that clicking on the station will popup a figure of the corresponding vertical component time-series. 

```{code-cell} ipython3
event = workspace.getEvent('uw10530748')
pstreams = workspace.getStreams('uw10530748', labels=['default'])
```

In order to handle lengthy time-series, we need disable the maximum row count of 5000 that altair uses to keep performance in check. There are alternative options that can be used to improve performance if we were working with a larger dataset. See the following documentation for more information: 

- [Why does Altair lead to such large notebooks?](https://altair-viz.github.io/user_guide/faq.html#altair-faq-large-notebook) 

```{code-cell} ipython3
alt.data_transformers.disable_max_rows()
```

The code below will generate the map and could be customized as the user desires.

```{code-cell} ipython3

station_map = folium.Map(
    location=[event.latitude, event.longitude], zoom_start=7, control_scale=True, tiles='cartodb positron'
)

lats = np.array([stream[0].stats.coordinates["latitude"] for stream in pstreams])
lons = np.array([stream[0].stats.coordinates["longitude"] for stream in pstreams])
stnames = np.array([stream[0].stats.station for stream in pstreams])
networks = np.array([stream[0].stats.network for stream in pstreams])

stations = pd.DataFrame(
    {
        "stnames": stnames,
        "network": networks,
        "coords":  zip(lats, lons),
    }
)
    
for i, r in stations.iterrows():
    st = ds.waveforms[r["network"]+'.'+r["stnames"]]['uw10530748_default']
    dd = pd.DataFrame({'times':st[2].times(),'Acceleration':st[2].data})
    chart = alt.Chart(dd).mark_line().encode(
        x='times',
        y='Acceleration',
        color=alt.value("#000000"))
    popup = folium.Popup()
    folium.features.VegaLite(chart, height=250, width=250).add_to(popup)
    folium.CircleMarker(
        location=r["coords"],
        tooltip=r["stnames"],
        popup=popup,
        color='green',
        fill=True,
        radius=6,
    ).add_to(station_map)
```

Finally, we display the map. When a station icon is clicked on, the corresponding vertical time-series will popup in a window.

```{code-cell} ipython3
station_map
```