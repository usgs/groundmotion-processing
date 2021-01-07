# Installation

## Dependencies

* Mac OSX, Windows, or Linux operating systems

* bash shell, gcc, git, curl

## Installing via conda

The conda package is the easiest way to install the code, but is not generally as up to
date as installing from the source code.

```bash
conda install gmprocess
```

## Installing from source

First clone this repository and go into the root directory with
```bash
git clone https://github.com/usgs/groundmotion-processing.git
cd groundmotion-processing
```

The `install.sh` script in the root directory of the package installs this package and all
other dependencies, including python and the required python libraries. It is regularly
tested on OSX, CentOS, and Ubuntu.

```bash
bash install.sh
```

Note: we are not yet able to test on Mac OS version newer than 10.14 because of institutional
restrictions. We have also had many bug reports from people who have tried to install our
code from source, typically related to the C compiler not being able to find header files.
The best we can do is point you to
[this](https://stackoverflow.com/questions/52509602/cant-compile-c-program-on-a-mac-after-upgrade-to-mojave)
discussion of the issue and hope that it help. Alernatively, you can install via conda.

## Tests

In the root directory of this repositry, you can run our unit tests with `pytest`:
```bash
py.test .
```
This will be followed by a lot of terminal output. Warnings are expected to occur and do
not indicate a problem. Errors indicate that something has gone wrong.
