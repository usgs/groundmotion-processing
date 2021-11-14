Overview
========

Objective
---------

The goal of this project is to update, restructure, and consolidate
existing USGS ground-motion processing software to incorporate recent
advances from researchers at the USGS, PEER, and others. It will
standardize tools for multiple USGS ground-motion products and enable
scientists within the USGS and the external community to develop and
expand ground-motion datasets used in many different
applications. Additionally, it will provide a standard interface for
local storage of recorded and synthetic ground-motion waveforms and
intensity metrics, as well as event and station metadata, in one
container that can be easily distributed. The resulting open-source
software will provide customizable processed ground-motion waveforms
and intensity metrics, while adhering to USGS software standards,
including documentation, peer review, testing, and continuous
integration.

.. image:: /_static/workspace.png
   :width: 700
   :alt: Diagram of workspace


Motivation
----------

* Facilitate creation of ground-motion data sets for multiple types of
  analysis.

* Leverage best practices from the community to standardize processing
  algorithms used in ShakeMap ground-motion processing software.

* Disentangle ground-motion processing (broad range of uses) from
  specific applications, e.g., ShakeMap generation.

Target Use Cases
----------------

* Standardize processing of ground-motion waveform data, including
  ground-motion simulations, for deriving a wide variety of Intensity
  Measure Types (IMTs) for real-time and simulation-based scenario
  ShakeMap production.

* Develop uniformly processed ground-motion data sets leveraging data
  from a variety of sources for use in development and analysis of
  ground-motion prediction equations, shaking duration, site response,
  testing of earthquake early warning algorithms, and testing seismic
  velocity models.

* Facilitate access to and routine processing of waveform and
  parametric data from a wide variety of data sources in many
  different formats, including COSMOS, PEER/NGA, CESMD/VDC, and
  international strong motion data sets. These parametric data can be
  formatted per-event or in the style of the NGA "flat" files.

* Convert files from any of the various strong-motion formats into a
  standard capable of being read by modern seismological processing
  software (i.e., Obspy).

* Facilitate the creation of relational databases containing relevant
  waveform metadata, stream/station metrics, etc.

Features
--------

* *gmprocess* is written in Python and builds upon
  `ObsPy <https://www.obspy.org>`_, 
  `PyASDF <https://seismicdata.github.io/pyasdf/>`_,  and
  `SEIS-PROV <http://seismicdata.github.io/SEIS-PROV/>`_.
  These libraries provide fundamental processing functionality, an HDF
  specification for seismic data, and a seismic standard for tracking 
  data provenance.

* The functionality can be accessed via Python libraries or through command
  line programs.

* We currently support Mac and Linux, and Windows systems.

* We provide file readers for many strong motion data formats that are not
  otherwise supported in ObsPy.

* We provide subclasses of ObsPy's ``Trace`` and ``Stream`` classes, 
  which are designed to aid analysis and metadata storage and validation 
  specifically for ground motion data that is organized by event. 

* We use the ASDF format to store earthquake metadata, station metadata,
  raw ground-motion time histories, processed ground-motion time histories,
  waveform and station metrics, and provenance information in a single,
  portable file.

* Import data from local filesystem using a wide variety of formats or
  retrieve data using web services from FDSN data centers.

* "Plug-and-play" architecture for efficiently evaluating data reprocessed
  with new or alternative algorithms.


.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
