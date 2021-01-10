# Initial Setup

In order to simplify the command line interface, the `gmrecords` command makes
use the "projects" and you can have many projects configured on your system.
A project is essentially a way to encapsulate the confiration and data 
directories so that they do not need to be specified as command line arguments.

There are two different types of projects:
 - ***directory projects*** - A directory project works by checking the current
   working directory for a project config file that holds the data and config 
   info. Thus, in order to activate the project, you have to be in that specific
   directory.
 - ***system-level projects*** - A system-level project works by checking the
   users home directory for a project config file that can hold many different
   configured projects. Thus, when you use a system-level project you can switch
   between different projects easily from any directory on your system.

When you create either type of project, you will be prompted to include your
name and email. This information is used for the data provenance. It is often
important to be able to track where data originated. If you do not which to 
share your personal information, we recommend using you institution/project 
name if possible.

To create a directory project, use the `init` gmrecords subcommand in the
where you would like to activate the project
```
$ gmrecords init
INFO 2021-01-06 16:38:40 | gmrecords.__init__: Logging level includes INFO.
INFO 2021-01-06 16:38:40 | init.main: Running subcommand 'init'

Created project: Project: local
	Conf Path: /Users/mrmanager/test_eqprocess/conf
	Data Path: /Users/mrmanager/test_eqprocess/data
Please enter your name and email. This informaitn will be added
to the config file and reported in the provenance of the data
processed in this project.
	Name: Mr Manager
	Email: mrmanager@gmrpocess.org
```

The `projects` subcommand is used for managing system-level projects. The
arguments are
```
$ eqprocess projects -h
usage: eqprocess projects [-h] [-l] [-s PROJECT] [-c] [-d PROJECT]

optional arguments:
  -h, --help            show this help message and exit
  -l, --list            List all configured eqprocess projects.
  -s PROJECT, --switch PROJECT
                        Switch from current project to PROJECT.
  -c, --create          Create a project and switch to it.
  -d PROJECT, --delete PROJECT
                        Delete existing project PROJECT.
```

Here is an example of creating a system-level project is
```
$ gmrecords projects -c
INFO 2021-01-06 16:41:21 | gmrecords.__init__: Logging level includes INFO.
INFO 2021-01-06 16:41:21 | projects.main: Running subcommand 'projects'
Please enter a project title: default
You will be prompted to supply two directories for this project:
 - A *config* path, which will store the gmprocess config files.
 - A *data* path, under which will be created directories for each
   event processed.
Please enter the conf path: [/Users/mrmanager/gmprocess_projects/default/conf]
Please enter the data path: [/Users/mrmanager/gmprocess_projects/default/data]

Created project: Project: default
	Conf Path: /Users/mrmanager/gmprocess_projects/default/conf
	Data Path: /Users/mrmanager/gmprocess_projects/default/data
Please enter your name and email. This informaitn will be added
to the config file and reported in the provenance of the data
processed in this project.
	Name: Mr Manager
	Email: mrmanager@gmprocess.org
```


## Sections in the configuration file

### fetchers

See "Fetching Data" section of the documentation.

### read

This section is for options when reading data. Currently we only have one option:

* `resample_rate` -- This is only used for data from older analog instruments that
   have been manually digitized and has uneven sample spacings. Currently we only
   support linear interpolation of unevent samples.

### windows


This section controls options regarding how the signal and noise windows are
selected. See the "Windowing data" subsection under "Processing steps" for
additional details.


### processing

This section is for processing steps that will affect the waveform and get
recorded as seismological provenance data. There are many available processing
steps, and the steps can be delete, commented out, and rearranged.

Please see the example config file for the list of supported steps, examples
of their use, and explanation of each step, as well as the "Waveform processing"
subsection under "Processing steps" for additional details.


### colocated

This section provides options for how to handle colocated instruments.

### duplicate

This section is for handling duplicate data. This comes up when a data center
provides the same data in multiple file formats, or when the same data is
provided by multiple data centers.

Since network codes are not reported reliably, we include methods for detecting
duplicates that does not rely on the network code being accurate. Options
include:

* `max_dist_tolerance` -- Maximum distance tolerance (in m) for duplicate data.

* `process_level_preference` -- Preference for selecting process level when
  faced with duplicate data but with different processing levels. Must be a list
  containing 'V0', 'V1', and 'V2'. The first item is the most preferred, and the
  last item is the least preferred.

* `format_preference` -- Analogous to process level preference, but for file
  formats. 


### build_report

This is for building a report, with a one-page summary of the data in each
StationStream per page. It will write out the latex file, and then look for
the `pdflatex` command and attempt to build the pdf. This requires
`summary_plots` to have been run. Currently we only support the `latex`
format but we expect to expand this in the near future.

### metrics

This section is for calculating waveform metrics and allows one to set
the output intensity measure types (IMTs) and output intensity measure
components (IMCs). See the comments in the config file for additional
explanation.

### pickers

This section is for options regarding the estimation of seismic phases,
which are used for setting the start time of the signal window. By
default, we first use use the travel time calculations given a 1D
velocity model, as implemented in teh `taup` package of ObsPy.

If the travel time calculation results in an arrival time prior to the
start of the record, then the other picker methods are evalulated, then
the other methods are evaluated and the one that results in the largest
signal-to-noise ration is preferred. 

