# Overview

This is a project designed to provide a number of functions related to
parsing and processing ground-motion data, building on top of the
[ObsPy](https://github.com/obspy/obspy/wiki) Python module. Most of
the extensions that we provide are to import data from a variety of
formats and perform standard processing, such as baseline correction,
computing ground-motion intensity measures and station metrics.

<figure>
  <img width="600px" src="figs/workspace.png" alt="Digagram of workspace"/>
</figure>

Current functionality includes:

* Readers for a variety of formats not supported by ObsPy. See the
  `gmprocess.io` subpackage. All readers return ObsPy streams.
* Ground-motion record summary methods (i.e., intensity measures or metrics)
  in `gmprocess.metrics` subpackage.
* The `gmprocess.processing.py` module uses ObsPy and our own methods for
  processing ground-motion records. We are working towards logging each
  processing step with the
  [SEIS-PROV](http://seismicdata.github.io/SEIS-PROV/index.html)
  provenance standard.
* We are also working towards storing records, event/station metadata, and
  provenance information in the
  [ASDF](https://seismic-data.org/) format. 


# Installation

See the top-level [README](https://github.com/usgs/groundmotion-processing).

# Workspace

* [Workspace](workspace.md)
