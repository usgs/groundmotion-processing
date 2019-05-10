# Features

* Storage of earthquake metadata, station metadata, raw ground-motion time histories, processed ground-motion time histories, waveform and station metrics, and provenance information in a single, portable file.

* Import data from local filesystem using a wide variety of formats or fetch data using web services from FDSN data centers.

* Can compute add additional waveform or station metrics by starting at an intermediate stage.

* Plug-and-play architecture for efficiently evaluating data reprocessed with new or alternative algorithms.

* Raw inputs are earthquake metadata, station metadata and ground-motion time histories directly from seismological sources; only downstream products need to be updated when earthquake or station metadata changes, e.g., revised earthquake location.

## Design

The code is written in Python and builds upon [ObsPy](https://github.com/obspy/obspy/wiki) and [PyASDF](https://seismic-data.org/), including [SEIS-PROV](http://seismicdata.github.io/SEIS-PROV/index.html) for storing provenance information.
