# Objective

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

<figure>
  <img src="figs/workspace.png" alt="Digagram of workspace"/>
</figure>

# Motivation

* Facilitate creation of ground-motion data sets for multiple types of
  analysis.

* Leverage best practices from the community to standardize processing
  algorithms used in ShakeMap ground-motion processing software.

* Disentangle ground-motion processing (broad range of uses) from
  specific applications, e.g., ShakeMap generation.

# Target Use Cases

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

