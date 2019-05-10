Warning
=======

This repository is currently under development so the functionality and
organization of the code is changing rapidly.


+---------------+----------------------+ 
| Linux build   | |Travis|             | 
+---------------+----------------------+ 
| Code quality  | |Codacy|             | 
+---------------+----------------------+ 
| Code coverage | |CodeCov|            | 
+---------------+----------------------+ 

.. |Travis| image:: https://travis-ci.com/usgs/groundmotion-processing.svg?branch=master
    :target: https://travis-ci.org/usgs/groundmotion-processing
    :alt: Travis Build Status

.. |Codacy| image:: https://api.codacy.com/project/badge/Grade/582cbceabb814eca9f708e37d6af9479
    :target: https://www.codacy.com/app/mhearne-usgs/groundmotion-processing?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=usgs/groundmotion-processing&amp;utm_campaign=Badge_Grade

.. |CodeCov| image:: https://codecov.io/gh/usgs/groundmotion-processing/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/usgs/groundmotion-processing
    :alt: Code Coverage Status


groundmotion-processing
=======================


Introduction
------------
This is a project designed to provide a number of functions related to parsing
and processing ground motion data, building on top of the 
`ObsPy <https://github.com/obspy/obspy/wiki>`_
library. Most of the extensions that we provide are to handle strong motion
data and related issues.

Current functionality includes:

- Readers for a variety of formats not supported by ObsPy. See the
  ``gmprocess.io`` subpackage. All readers return ObsPy streams.
- Ground motion record summary methods (i.e., intensity measures, or metrics)
  in ``gmprocess.metrics`` subpackage.
- The ``gmprocess.processing.py`` module uses ObsPy and our own methods for
  processing ground motion records. We are working towards logging each
  processing step with the
  `SEIS-PROV <http://seismicdata.github.io/SEIS-PROV/index.html>`_
  provenance standard.
- We are also working towards storing records, event/station metadata, and
  provenance information in the
  `ASDF <https://seismic-data.org/>`_ format. 


Installation and Dependencies
-----------------------------

- Mac OSX or Linux operating systems
- bash shell, gcc, git, curl
- On OSX, Xcode and command line tools
- The ``install.sh`` script installs this package and all other dependencies,
  including python and the required python libraries. It is regularly tested
  on OSX, CentOS, and Ubuntu.
- Alternative install with conda: 
.. code-block::

    conda install gmprocess

- Run ``gmsetup`` to install config files in the ``.gmprocess`` subdirectory under
  the home directory.

