#!/bin/bash

unamestr=`uname`
if [ "$unamestr" == 'Linux' ]; then
    prof=~/.bashrc
    mini_conda_url=https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
    matplotlibdir=~/.config/matplotlib
    CC=gcc_linux-64
elif [ "$unamestr" == 'FreeBSD' ] || [ "$unamestr" == 'Darwin' ]; then
    prof=~/.bash_profile
    mini_conda_url=https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
    matplotlibdir=~/.matplotlib
    CC=gcc
else
    echo "Unsupported environment. Exiting."
    exit
fi

source $prof

# Name of virtual environment
VENV=gmprocess

# create a matplotlibrc file with the non-interactive backend "Agg" in it.
if [ ! -d "$matplotlibdir" ]; then
    mkdir -p $matplotlibdir
fi
matplotlibrc=$matplotlibdir/matplotlibrc
if [ ! -e "$matplotlibrc" ]; then
    echo "backend : Agg" > "$matplotlibrc"
    echo "NOTE: A non-interactive matplotlib backend (Agg) has been set for this user."
elif grep -Fxq "backend : Agg" $matplotlibrc ; then
    :
elif [ ! grep -Fxq "backend" $matplotlibrc ]; then
    echo "backend : Agg" >> $matplotlibrc
    echo "NOTE: A non-interactive matplotlib backend (Agg) has been set for this user."
else
    sed -i '' 's/backend.*/backend : Agg/' $matplotlibrc
    echo "###############"
    echo "NOTE: $matplotlibrc has been changed to set 'backend : Agg'"
    echo "###############"
fi

developer=0
while getopts p:d FLAG; do
  case $FLAG in
    d)
        echo "Installing developer packages."
        developer=1
      ;;
  esac
done


# Is conda installed?
conda --version
if [ $? -ne 0 ]; then
    echo "No conda detected, installing miniconda..."

    command -v curl >/dev/null 2>&1 || { echo >&2 "Script requires curl but it's not installed. Aborting."; exit 1; }

    curl $mini_conda_url -o miniconda.sh;
    # if curl fails, bow out gracefully
    if [ $? -ne 0 ];then
        echo "Failed to download miniconda installer shell script. Exiting."
        exit 1
    fi

    echo "Install directory: $HOME/miniconda"

    bash miniconda.sh -f -b -p $HOME/miniconda

    # if miniconda.sh fails, bow out gracefully
    if [ $? -ne 0 ];then
        echo "Failed to run miniconda installer shell script. Exiting."
        exit 1
    fi


    # Need this to get conda into path
    . $HOME/miniconda/etc/profile.d/conda.sh

    # remove the shell script
    rm miniconda.sh
else
    echo "conda detected, installing $VENV environment..."
fi


echo "Installing packages from conda-forge"


# Choose an environment file based on platform
# only add this line if it does not already exist
grep "/etc/profile.d/conda.sh" $prof
if [ $? -ne 0 ]; then
    echo ". $_CONDA_ROOT/etc/profile.d/conda.sh" >> $prof
fi


# Start in conda base environment
echo "Activate base virtual environment"
conda activate base

# Remove existing environment if it exists
conda remove -y -n $VENV --all

dev_list=(
    "autopep8"
    "flake8"
    "pyflakes"
    "rope"
    "yapf"
)


package_list=(
    "$CC"
    "cython"
    "flake8"
    "impactutils"
    "ipython"
    "jupyter"
    "libcomcat"
    "lxml"
    "matplotlib"
    "'numpy<1.17'"
    "openpyxl"
    "openquake.engine"
    "pandas"
    "proj4=6.1.0"
    "pyasdf"
    "pytest"
    "pytest-cov"
    "python>=3.6"
    "pyyaml"
    "requests"
    "vcrpy"
)


if [ $developer == 1 ]; then
    package_list=( "${package_list[@]}" "${dev_list[@]}" )
    echo ${package_list[*]}
fi


# Create a conda virtual environment
echo "Creating the $VENV virtual environment:"
conda create -y -n $VENV -c conda-forge \
      --channel-priority ${package_list[*]}

# Bail out at this point if the conda create command fails.
# Clean up zip files we've downloaded
if [ $? -ne 0 ]; then
    echo "Failed to create conda environment.  Resolve any conflicts, then try again."
    exit
fi


# Activate the new environment
echo "Activating the $VENV virtual environment"
conda activate $VENV



# if conda activate fails, bow out gracefully
if [ $? -ne 0 ];then
    echo "Failed to activate ${VENV} conda environment. Exiting."
    exit 1
fi

# upgrade pip, mostly so pip doesn't complain about not being new...
pip install --upgrade pip

# if pip upgrade fails, complain but try to keep going
if [ $? -ne 0 ];then
    echo "Failed to upgrade pip, trying to continue..."
    exit 1
fi

# The presence of a __pycache__ folder in bin/ can cause the pip
# install to fail... just to be safe, we'll delete it here.
if [ -d bin/__pycache__ ]; then
    rm -rf bin/__pycache__
fi

# use pip to install obspy 1.1.1
pip install obspy==1.1.1

# This package
echo "Installing ${VENV}..."
pip install -e .

# if pip install fails, bow out gracefully
if [ $? -ne 0 ];then
    echo "Failed to pip install this package. Exiting."
    exit 1
fi

# Tell the user they have to activate this environment
echo "Type 'conda activate $VENV' to use this new virtual environment."
