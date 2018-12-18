
Status
=======
[![Build Status](https://travis-ci.org/usgs/groundmotion-processing.svg?branch=master)](https://travis-ci.org/usgs/groundmotion-processing)

[![codecov](https://codecov.io/gh/usgs/groundmotion-processing/branch/master/graph/badge.svg)](https://codecov.io/gh/usgs/groundmotion-processing)

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/582cbceabb814eca9f708e37d6af9479)](https://www.codacy.com/app/mhearne-usgs/groundmotion-processing?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=usgs/groundmotion-processing&amp;utm_campaign=Badge_Grade)


groundmotion-processing
=====

Read and process ground motion amplitude data.

# Introduction

groundmotion-processing is a project designed to provide a number of
functions related to parsing and processing strong ground motion data.

# Installing

#### If you already have a miniconda or anaconda Python 3.5 environment:

Conda install:
- `conda install gmprocess`

Automated install:
- `git clone https://github.com/usgs/groundmotion-processing.git`
- `cd groundmotion-processing`
- `bash intall.sh`
- `conda activate gmprocess`

Manual install:
 - `conda install numpy`
 - `conda install pandas`
 - `conda install openpyxl`
 - `conda install lxml`
 - `pip install git+https://github.com/usgs/groundmotion-processing.git`


#### If you do not have anaconda or miniconda, but have Python 3.5 installed with pip:
 - `pip install numpy`
 - `pip install pandas`
 - `pip install openpyxl`
 - `pip install lxml`
 - `pip install git+https://github.com/usgs/groundmotion-processing.git`

## Updating

Updating conda install:
- `conda update gmprocess`

Updating automated install:
- `cd groundmotion-processing`
- `git pull --ff-only https://github.com/usgs/groundmotion-processing.git master`
- `bash install.sh`

Updating manually installed:
 - `pip install --upgrade git+https://github.com/usgs/groundmotion-processing.git`


# Developer notes

### Readers
The data file readers are modeled after obspy file readers, and have a standard interface.

Data file readers are located in `gmprocess/io/[format]/core.py`.

This core.py module should take the following form:
<pre>
def is_format(filename):
    # code to examine candidate file and determine if it is of the type specified.
    # return True if file is correct type, False otherwise.

def read_format(filename,**kwargs):
    # code to read file and return an obspy Stream object.
</pre>

### Intensity measurement types

In order to add an intensity measurement types (IMT) calculation, add
a file with the type as the file name under pgm/imt/. The calculation
should be called calculate_[TYPE], where [TYPE] matches the file
name. The argument should always be *stream*. The second function
should always be *imcs* (a list of requested components). All other
functions in the file should be hidden by an underscore (example `def
_get_horizontals(stream)`). The calculate function should return a
dictionary of each component and the resulting values. Example:

<pre>
{
    'HN2': 81.234,
    'GMROTD0.0': 86.784,
    'GMROTD100.0': 96.446,
    'HN1': 99.249,
    'HNZ': 183.772,
    'GMROTD50.0': 92.177,
    'GREATER_OF_TWO_HORIZONTALS': 99.249
}
</pre>
StationSummary should be updated to handle the new IMT in `gather_pgms`.

### Intensity measurement components

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
99.249

Channels example:
<pre>
{
    'HN1': 99.249,
    'HN2': 81.234,
    'HNZ': 183.772
}
</pre>

GMRotD example:
<pre>
{
    0.0: 103.299,
    50.0: 119.925,
    100.0: 125.406
}
</pre>



#### For examples of the API see the [example notebooks](https://github.com/usgs/groundmotion-processing/tree/master/notebooks).
<!-- You will not be able to see this text. -->
