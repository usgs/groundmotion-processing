Introduction
------------
This is a project designed to provide a number of functions related to parsing
and processing ground motion data, building on top of the 
`ObsPy <https://github.com/obspy/obspy/wiki>`_
library. Most of the extensions that we provide are to handle strong motion
data and related issues.


Documentation
-------------
https://usgs.github.io/groundmotion-processing/


Build info
----------

+---------+------------------+-----------------+------------+
| Azure   | |AzureM1015P37|  | OSX 10.15       | Python 3.7 |
+         +------------------+-----------------+------------+
|         | |AzureM1015P38|  | OSX 10.15       | Python 3.8 |
+         +------------------+-----------------+------------+
|         | |AzureM1014P37|  | OSX 10.14       | Python 3.7 |
+         +------------------+-----------------+------------+
|         | |AzureM1014P38|  | OSX 10.14       | Python 3.8 |
+         +------------------+-----------------+------------+
|         | |AzureLP37|      | ubuntu          | Python 3.7 |
+         +------------------+-----------------+------------+
|         | |AzureLP38|      | ubuntu          | Python 3.8 |
+---------+------------------+-----------------+------------+
| Travis  | |Travis|         | ubuntu          | Python 3.7 |
+---------+------------------+-----------------+------------+
| Codacy  | |Codacy|                                        |
+---------+-------------------------------------------------+
| CodeCov | |CodeCov|                                       |
+---------+-------------------------------------------------+

.. |Travis| image:: https://travis-ci.com/usgs/groundmotion-processing.svg?branch=master
    :target: https://travis-ci.org/usgs/groundmotion-processing
    :alt: Travis Build Status

.. |Codacy| image:: https://api.codacy.com/project/badge/Grade/582cbceabb814eca9f708e37d6af9479
    :target: https://www.codacy.com/app/mhearne-usgs/groundmotion-processing?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=usgs/groundmotion-processing&amp;utm_campaign=Badge_Grade

.. |CodeCov| image:: https://codecov.io/gh/usgs/groundmotion-processing/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/usgs/groundmotion-processing
    :alt: Code Coverage Status

.. |AzureM1015P37| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20MacOS_10_15_Python37
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Azure DevOps Build Status                                             

.. |AzureM1015P38| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20MacOS_10_15_Python38
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Azure DevOps Build Status                                             

.. |AzureM1014P37| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20MacOS_10_14_Python37
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Azure DevOps Build Status                                             

.. |AzureM1014P38| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20MacOS_10_14_Python38
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Azure DevOps Build Status                                             

.. |AzureLP37| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20Linux_Python37
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Azure DevOps Build Status                                             

.. |AzureLP38| image:: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_apis/build/status/usgs.groundmotion-processing?branchName=master&jobName=gmprocess&configuration=gmprocess%20Linux_Python38
   :target: https://dev.azure.com/GHSC-ESI/USGS-groundmotion-processing/_build/latest?definitionId=5&branchName=master
   :alt: Azure DevOps Build Status                                             
