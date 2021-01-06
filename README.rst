.. raw:: html

   <embed>
      <div>
      <img style="vertical-align:middle" src="docs/images/gmprocess_logo_large.png" height="50px">
      </div>
   </embed>


Introduction
------------
This is a project designed to provide a number of functions related to parsing
and processing earthquake ground motion data, building on top of the 
`ObsPy <https://github.com/obspy/obspy/wiki>`_
library. Most of the extensions that we provide are to handle strong motion
data and related issues.


Documentation
-------------
- Please note, we are in the process of improving the documentation.
- The manual is available
  `here <https://usgs.github.io/groundmotion-processing/>`_.
- Also, please see the 
  `Wiki <https://github.com/usgs/groundmotion-processing/wiki>`_ 
  as a "quick start" guide.


Build info
----------

We are in the process of trying to support Windows. As the table below shows, 
we are still not able to pass all tests on Windows OS yet. 

+---------+------------------+-----------------+------------+
| Azure   | |AzureM1015P37|  | OSX 10.15       | Python 3.7 |
+         +------------------+-----------------+------------+
|         | |AzureM1015P38|  | OSX 10.15       | Python 3.8 |
+         +------------------+-----------------+------------+
|         | |AzureWP37|      | Windows-latest  | Python 3.7 |
+         +------------------+-----------------+------------+
|         | |AzureWP38|      | Windows-latest  | Python 3.8 |
+         +------------------+-----------------+------------+
|         | |AzureLP37|      | ubuntu-latest   | Python 3.7 |
+         +------------------+-----------------+------------+
|         | |AzureLP38|      | ubuntu-latest   | Python 3.8 |
+---------+------------------+-----------------+------------+
| Codacy  | |Codacy|                                        |
+---------+-------------------------------------------------+
| CodeCov | |CodeCov|                                       |
+---------+-------------------------------------------------+

.. |Codacy| image:: https://api.codacy.com/project/badge/Grade/582cbceabb814eca9f708e37d6af9479
    :target: https://www.codacy.com/app/mhearne-usgs/groundmotion-processing?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=usgs/groundmotion-processing&amp;utm_campaign=Badge_Grade

.. |CodeCov| image:: https://codecov.io/gh/usgs/groundmotion-processing/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/usgs/groundmotion-processing
    :alt: Code Coverage Status

.. |AzureM1015P37| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20MacOS_py37
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Build Status: Mac 10.15, python 3.7

.. |AzureM1015P38| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20MacOS_py38
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Build Status: Mac 10.15, python 3.8

.. |AzureWP37| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20Windows_py37
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Build Status: windows-latest, python 3.7

.. |AzureWP38| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20Windows_py38
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Build Status: windows-latest, python 3.8

.. |AzureLP37| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20Linux_py37
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Build Status: ubuntu-latest, python 3.7

.. |AzureLP38| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20Linux_py38
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Build Status: ubuntu-latest, python 3.8
