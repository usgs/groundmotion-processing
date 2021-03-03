.. raw:: html

   <embed>
      <div>
      <img style="vertical-align:middle" src="docs/_static/gmprocess_logo_large.png" height="50px">
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
- Please note, we are in the process of improving the documentation and that
  there are some incomplete sections.
- The full documentation is available
  `here <https://gmprocess.readthedocs.io/en/latest/index.html>`_.


Reference
---------
If you wish to cite this software, please use this reference:

- Hearne, M., E. M. Thompson, H. Schovanec, J. Rekoske, B. T. Aagaard, and C. B. 
  Worden (2019). USGS automated ground motion processing software, USGS 
  Software Release, 
  doi: `10.5066/P9ANQXN3 <https://dx.doi.org/10.5066/P9ANQXN3>`_.


Build info
----------

+---------+------------------+-----------------+------------+
| Azure   | |AzureM1015P37|  | OSX 10.15       | Python 3.7 |
+         +------------------+-----------------+------------+
|         | |AzureM1015P38|  | OSX 10.15       | Python 3.8 |
+         +------------------+-----------------+------------+
|         | |AzureM1015P39|  | OSX 10.15       | Python 3.9 |
+         +------------------+-----------------+------------+
|         | |AzureWP37|      | Windows-latest  | Python 3.7 |
+         +------------------+-----------------+------------+
|         | |AzureWP38|      | Windows-latest  | Python 3.8 |
+         +------------------+-----------------+------------+
|         | |AzureWP39|      | Windows-latest  | Python 3.9 |
+         +------------------+-----------------+------------+
|         | |AzureLP37|      | ubuntu-latest   | Python 3.7 |
+         +------------------+-----------------+------------+
|         | |AzureLP38|      | ubuntu-latest   | Python 3.8 |
+---------+------------------+-----------------+------------+
|         | |AzureLP39|      | ubuntu-latest   | Python 3.9 |
+---------+------------------+-----------------+------------+
| Codacy  | |Codacy|                                        |
+---------+-------------------------------------------------+
| CodeCov | |CodeCov|                                       |
+---------+-------------------------------------------------+
| Docs    | |readthedocs|                                   +
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

.. |AzureM1015P39| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20MacOS_py39
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Build Status: Mac 10.15, python 3.9

.. |AzureWP37| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20Windows_py37
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Build Status: windows-latest, python 3.7

.. |AzureWP38| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20Windows_py38
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Build Status: windows-latest, python 3.8

.. |AzureWP39| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20Windows_py39
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Build Status: windows-latest, python 3.9

.. |AzureLP37| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20Linux_py37
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Build Status: ubuntu-latest, python 3.7

.. |AzureLP38| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20Linux_py38
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Build Status: ubuntu-latest, python 3.8

.. |AzureLP39| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20Linux_py39
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Build Status: ubuntu-latest, python 3.9

.. |readthedocs| image:: https://readthedocs.org/projects/gmprocess/badge/?version=latest
   :target: https://gmprocess.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status