# Installation

:::{important}
Previously we used `conda` to manage dependencies but that was creating some difficulties, so we are now relying on `pip` as much as possible.
We hope to be able to provide `pip` installs via pypi wheels soon.

Our development team is not proficient with Windows systems, so our ability to support Windows installs is limited.
We have done our best to provide instructions to support Windows build.
:::

:::{danger}
There is an old gmprocess package available via conda.
Please do not install it!
It is very out of date and won't work.
:::

We recommend installing gmprocess into a virtual environment to isolate your code from other projects that might create conflicts.
You can use the Python3 [`venv`](https://docs.python.org/3/library/venv.html) module or [conda](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) to create and manage virtual environments.
Conda generally uses more space on your filesystem, but it can install more dependencies.

## Installing from source

:::{admonition} Prerequisites
:class: note

```{tab} Linux
- A C compiler (typically gcc).
- Bash shell, curl, and git.

Most Linux distributions include these tools in the default installation.
```

```{tab} macOS
- A C compiler.
- Bash shell, curl, and git.

The easiest way to install these tools is to install the XCode Command Line Tools.
Simply run `git`, and instructions for installing the Command Line Tools will be displayed if it is not installed.

Some pypi wheels are not yet available for the macOS arm64 architecture.
As a result, some dependencies will be built from source when installing via `pip`.
Building the `fiona` package from source requires `GDAL`, which is a C++ library that can be installed manually or using conda.
```

```{tab} Windows
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html#windows-installers) 
  (recommended) or [anaconda](https://www.anaconda.com/products/distribution).
- A C compiler. We have had success following 
  [these instructions](https://wiki.python.org/moin/WindowsCompilers).
- Git and some kind of console.

There is one dependency ([fiona](https://pypi.org/project/Fiona/)) that we have not been able to install with pip on Windows systems. So we rely on conda for this.
Start a conda session and run `conda init powershell`.
Then open a new powershell terminal and run `conda create --name gmprocess python=3.8 pip fiona` and `conda activate gmprocess`.
```

:::

First clone this repository and go into the root directory with

```{code-block} console
git clone https://github.com/usgs/groundmotion-processing.git
cd groundmotion-processing
```

:::{admonition} Windows
:class: important
:::

Next, install the code with pip

```{code-block} console
pip install .
```

Note that this will install the minimum requirements to run the code.
There are additional optional packages that can be installed that support running the unit tests (`test`), code development (`dev`), building wheels (`build`), and building the documentation (`doc`).
To install these, you need to add the relevant option in brackets:

```{code-block} console
pip install .[test,dev,doc,build]
```

For developers, it is also convenient to install the code in "editable" mode by adding the `-e` option:

```{code-block} console
pip install -e .[test,dev,doc]
```

## Tests

If you included the optional `test` dependencies in the install step, then you can run the unit tests in the root directory of the repository:

```{code-block} console
pytest .
```

This will be followed by a lot of terminal output.
Warnings are expected to occur and do not indicate a problem.
Errors indicate that something has gone wrong and you will want to troubleshoot.
You can create an issue in [GitHub](https://github.com/usgs/groundmotion-processing/issues) if you are not able to resolve the problem.
