# Configuration File

The config file is the primary means by which users can adjust and customize
*gmprocess*. While the config file includes comments to help explain the values
and their units, the config file in the repository 
[here](https://github.com/usgs/groundmotion-processing/blob/master/gmprocess/data/config_production.yml)
is also a useful reference because sections or comments can be removed from the
config file for a given project. Also, the config file in the repository should
stay updated when the code changes. An outdated config file is a common source 
of confusion when updating *gmprocess* because updating the code does not update
the config file that is installed for existing projects and so the config will
get out of date.

The following sections correspond to the top-level sections of the config file.
Click on the section for more details. 

```{toctree}
---
maxdepth: 1
---
   user <conf_file/user>
   fetchers <conf_file/fetchers>
   read <conf_file/read>
   windows <conf_file/windows>
   processing <conf_file/processing>
   colocated <conf_file/colocated>
   duplicate <conf_file/duplicate>
   build_report <conf_file/build_report>
   metrics <conf_file/metrics>
   pickers <conf_file/pickers>
```


% Indices and tables

% ==================

% * :ref:`genindex`

% * :ref:`modindex`

% * :ref:`search`
