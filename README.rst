+---------------+----------------------+ 
| Linux build   | |Travis|             | 
+---------------+----------------------+ 
| Code quality  | |Codacy|             | 
+---------------+----------------------+ 
| Code coverage | |CodeCov|            | 
+---------------+----------------------+ 
| Manage issues | |Waffle|             | 
+---------------+----------------------+ 

.. |Travis| image:: https://travis-ci.com/usgs/groundmotion-processing.svg?branch=master
    :target: https://travis-ci.org/usgs/groundmotion-processing
    :alt: Travis Build Status

.. |CodeCov| image:: https://codecov.io/gh/usgs/groundmotion-processing/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/usgs/groundmotion-processing
    :alt: Code Coverage Status

.. |Codacy| image:: https://api.codacy.com/project/badge/Grade/582cbceabb814eca9f708e37d6af9479
    :target: https://www.codacy.com/app/mhearne-usgs/groundmotion-processing?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=usgs/groundmotion-processing&amp;utm_campaign=Badge_Grade

.. |Waffle| image:: https://badge.waffle.io/usgs/groundmotion-processing.svg?columns=all
    :target: https://waffle.io/usgs/groundmotion-processing
    :alt: 'Waffle.io - Columns and their card count'



groundmotion-processing
=======================
Read and process ground motion amplitude data.



Introduction
------------
This is a project designed to provide a number of functions related to parsing
and processing strong ground motion data.


Installation and Dependencies
-----------------------------

- Mac OSX or Linux operating systems
- bash shell, gcc, git, curl
- On OSX, Xcode and command line tools
- The ``install.sh`` script installs this package and all other dependencies,
  including python and the required python libraries. It is regularly tested
  on OSX, CentOS, and Ubuntu.
- Alternative install with conda: `conda install gmprocess`


Developer notes
---------------

Readers
~~~~~~~
The data file readers are modeled after obspy file readers, and have a standard interface.

Data file readers are located in `gmprocess/io/[format]/core.py`.

This core.py module should take the following form:
```
def is_format(filename):
    # code to examine candidate file and determine if it is of the type specified.
    # return True if file is correct type, False otherwise.

def read_format(filename,**kwargs):
    # code to read file and return an obspy Stream object.
```


Intensity measurement types
~~~~~~~~~~~~~~~~~~~~~~~~~~~
In order to add an intensity measurement types (IMT) calculation, add
a file with the type as the file name under pgm/imt/. The calculation
should be called calculate_[TYPE], where [TYPE] matches the file
name. The argument should always be *stream*. The second function
should always be *imcs* (a list of requested components). All other
functions in the file should be hidden by an underscore (example `def
_get_horizontals(stream)`). The calculate function should return a
dictionary of each component and the resulting values.

Example:

```
{
    'HN2': 81.234,
    'GMROTD0.0': 86.784,
    'GMROTD100.0': 96.446,
    'HN1': 99.249,
    'HNZ': 183.772,
    'GMROTD50.0': 92.177,
    'GREATER_OF_TWO_HORIZONTALS': 99.249
}
```

StationSummary should be updated to handle the new IMT in `gather_pgms`.


Intensity measurement components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In order to add an intensity measurement component (IMC) calculation,
add a file with the component as the file name under pgm/imc/. The
calculation should be called calculate_[COMPONENT], where [COMPONENT]
matches the file name. The argument should always be *stream*. All
other functions in the file should be hidden by an underscore (example
`def _get_horizontals(stream)`). The calculate function should return
a single value or a dictionary of each component and the resulting
values. Imt calculations should be updated to handle a dictionary if
one is returned. Otherwise, single values will automatically be
handled.

Greater of two horizontals example:
```
99.249
```

Channels example:
```
{
    'HN1': 99.249,
    'HN2': 81.234,
    'HNZ': 183.772
}
```

GMRotD example:
```
{
    0.0: 103.299,
    50.0: 119.925,
    100.0: 125.406
}
```


For examples of the API see the
`example notebooks<https://github.com/usgs/groundmotion-processing/tree/master/notebooks>`_.

