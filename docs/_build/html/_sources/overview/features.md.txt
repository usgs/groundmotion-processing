# Features

* The software is written in Python and builds upon
  [ObsPy](https://www.obspy.org) and
  [PyASDF](https://seismicdata.github.io/pyasdf/),
  including [SEIS-PROV](http://seismicdata.github.io/SEIS-PROV/index.html)
  for storing provenance information.

* The functionality can be accessed via Python libraries or through command
  line programs.

* We currently support Mac and Linux, and Windows systems.

* We provide file readers for many strong motion data formats that are not
  otherwise supported in ObsPy.

* We provide subclasses of ObsPy's `Trace` and `Stream` classes, which are
  designed to aid analysis and metadata storage and validation specifically for
  ground motion data that is organized by event. 

* We use the ASDF format to store earthquake metadata, station metadata,
  raw ground-motion time histories, processed ground-motion time histories,
  waveform and station metrics, and provenance information in a single,
  portable file.

* Import data from local filesystem using a wide variety of formats or
  retrieve data using web services from FDSN data centers.

* "Plug-and-play" architecture for efficiently evaluating data reprocessed
  with new or alternative algorithms.

