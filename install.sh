#!/bin/bash

unamestr=`uname`
if [ "$unamestr" == 'Linux' ]; then
    prof=~/.bashrc
    mini_conda_url=https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
    matplotlibdir=~/.config/matplotlib
elif [ "$unamestr" == 'FreeBSD' ] || [ "$unamestr" == 'Darwin' ]; then
    prof=~/.bash_profile
    mini_conda_url=https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
    matplotlibdir=~/.matplotlib
else
    echo "Unsupported environment. Exiting."
    exit
fi

CC_PKG=c-compiler

source $prof

# Name of virtual environment
VENV=gmprocess

developer=0
py_ver=3.9
while getopts p:d FLAG; do
  case $FLAG in
    p)
        py_ver=$OPTARG
      ;;
  esac
done

echo "Using python version $py_ver"

# create a matplotlibrc file with the non-interactive backend "Agg" in it.
if [ ! -d "$matplotlibdir" ]; then
    mkdir -p $matplotlibdir
    if [ $? -ne 0 ];then
        echo "Failed to create matplotlib configuration file. Exiting."
        exit 1
    fi
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


# Is conda installed?
conda --version
if [ $? -ne 0 ]; then
    echo "No conda detected, installing miniconda..."

    command -v curl >/dev/null 2>&1 || { echo >&2 "Script requires curl but it's not installed. Aborting."; exit 1; }

    curl -L $mini_conda_url -o miniconda.sh;

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

echo "Installing mamba from conda-forge"

conda install mamba -y -n base -c conda-forge

echo "Installing packages from conda-forge"

# Choose an environment file based on platform
# only add this line if it does not already exist
grep "/etc/profile.d/conda.sh" $prof
if [ $? -ne 0 ]; then
    echo ". $_CONDA_ROOT/etc/profile.d/conda.sh" >> $prof
fi


# Start in conda base environment
echo "Activate base virtual environment"
eval "$(conda shell.bash hook)"                                                
conda activate base

# Remove existing environment if it exists
conda remove -y -n $VENV --all


# Create a conda virtual environment
conda config --add channels 'defaults'
conda config --add channels 'conda-forge'
conda config --set channel_priority strict

echo "Creating the $VENV virtual environment:"
# conda create -n $VENV -y --file requirements.txt
mamba create -n $VENV -y --file requirements.txt

# Bail out at this point if the conda create command fails.
# Clean up zip files we've downloaded
if [ $? -ne 0 ]; then
    echo "Failed to create conda environment.  Resolve any conflicts, then try again."
    exit 1
fi


# Activate the new environment
echo "Activating the $VENV virtual environment"
conda activate $VENV

# if conda activate fails, bow out gracefully
if [ $? -ne 0 ];then
    echo "Failed to activate ${VENV} conda environment. Exiting."
    exit 1
fi

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

# This package
echo "Installing ${VENV}..."

##################### Try to get in front of missing/wrong C compiler issues #######
clang_exists=0
clang_path=`which clang`
if [ -n "${clang_path}" ]; then
    clang_exists=1
    echo "clang is installed on your system."
fi

gcc_exists=0
gcc_path=`which gcc`
if [ -n "$gcc_path" ]; then
    gcc_exists=1
    echo "gcc is installed on your system."
fi

if [ clang_exists == 0 ] && [ gcc_exists == 0 ]; then
    echo "You are missing a C compiler. Please install either gcc or clang."
    exit 1
fi

# test to see if CC is set
# https://stackoverflow.com/a/13864829
cc_set=0
x=""
if [ -n "${CC}" ]; then # if $CC is set
    cc_set=1
    echo "CC is set to '${CC}'"
fi

if [ $cc_set == 0 ]; then
    if [ $clang_exists == 1 ];then
        export CC=clang
    else
        export CC=gcc
    fi
    echo "Using ${CC} as C compiler"
else
    echo "CC is set to ${CC} already."
fi
##################### Try to get in front of missing/wrong C compiler issues #######

pip install -e .

# if pip install fails, bow out gracefully
if [ $? -ne 0 ];then
    echo "Failed to pip install this package. Exiting."
    exit 1
fi

# Tell the user they have to activate this environment
echo "Type 'conda activate $VENV' to use this new virtual environment."
