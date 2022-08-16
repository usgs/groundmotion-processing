# Installation

Note that we used to use conda to manage dependencies but that was creating some
difficulties and so we are now relying on pip as much as possible. 

```{caution}
There is an old gmprocess package available via conda. Please do not install this!
It is very out of date and won't work.
```

However, we do recommend installing gmprocess into a virtual environment to isolate
your code from other projects that might create conflicts and 
[conda](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)
is good option for accomplishing this.

We hope to be able to provide pip installs via pypi wheels soon.

## Installing from source

:::{admonition} Prerequisites
:class: note

```{tab} Mac and Linux
- A C compiler. On a mac, this usually means installing XCode/Comomand Line tools. 
  For linux, it depends on the type of linux but is usually very stright forward.
- Bash shell, curl, and git.
```

```{tab} Windows
- A C compiler. We have had success follwing 
  [these instructions](https://github.com/cython/cython/wiki/CythonExtensionsOnWindows#using-windows-sdk-cc-compiler-works-for-all-python-versions)
  from cython.
- Git and some kind of console.

Our development team is not proficient with Windows systems, so our ability to 
support Windows installs is limited. But we know that the code compiles and 
passes tests in Windows on our continuous integration systems.
```
:::

First clone this repository and go into the root directory with

```
$ git clone https://github.com/usgs/groundmotion-processing.git
$ cd groundmotion-processing
```

:::{admonition} Windows
:class: important
There is one depenency ([fiona](https://pypi.org/project/Fiona/)) that we have not been
able to install with pip on Windows systems. So we rely on conda for this.
```
$ conda create --name gmprocess python=3.8 pip fiona 
$ call activate gmprocess
```
:::

Next, install the code with pip
```
$ pip install .
```

Note that this will install the minimum requirements to run the code. There are 
additional optional packages that can be installed that support running the unit tests 
(`test`), code development (`dev`), buliding wheels (`build`), and building the 
documentation (`doc`). To install these, you need to add the relevant option in 
brackets:

```
$ pip install .[test,dev,doc,build]
```

For developers, it is also conveninet to install the code in "editable" mode by adding
the `-e` option:

```
$ pip install -e .[test,dev,doc]
```

## Tests

If you included the optional `test` dependencies in the install step, then you can run
the unit tests  in the root directory of this repositry:

```
$ py.test .
```

This will be followed by a lot of terminal output. Warnings are expected to occur and 
do not indicate a problem. Errors indicate that something has gone wrong and you will 
want to troubleshoot. You can create an issue in github if you are not able to resolve
the problem.

