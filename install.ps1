#!/bin/bash

$mini_conda_url="https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"


Write-Output "Path:"
Write-Output $env:Path

$VENV="gmprocess"
$py_ver="3.7"
$CC_PKG="c-compiler"

# Is conda installed?
If ($null -eq (Get-Command "conda" -ErrorAction SilentlyContinue)){
    Write-Output "No conda detected, installing miniconda..."
    Write-Output "Install directory: $HOME/miniconda"
    Invoke-WebRequest -Uri $mini_conda_url -OutFile ".\condainstall.exe"
    Start-Process -FilePath ".\condainstall.exe" -PassThru -Wait -ArgumentList "/S /AddToPath=1"
}Else{
    Write-Output "conda detected, installing $VENV environment..."
}
# So that the path is updated
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine")
$conda_path = Write-Output $env:CONDA_PREFIX
$env:Path += ";$conda_path"
conda --version
Write-Output "PATH:"
Write-Output $env:PATH
Write-Output ""
# Start in conda base environment
Write-Output "Activate base virtual environment"
# conda activate base
# Remove existing environment if it exists
conda remove -y -n $VENV --all
# Package list:
$package_list=
    "python=$py_ver",
    "$CC_PKG",
    "cython",
    "impactutils",
    "ipython",
    "jupyter",
    "libcomcat",
    "lxml",
    "mapio",
    "matplotlib",
    "numpy",
    "obspy>=1.2.1",
    "openpyxl",
    "pandas",
    "ps2ff",
    "pyasdf",
    "pytest",
    "pytest-cov",
    "pyyaml",
    "requests",
    "vcrpy",
    "pip"

# Create a conda virtual environment
Write-Output "Creating the $VENV virtual environment:"
Write-Output "conda create -y -n $VENV -c conda-forge --channel-priority $package_list"
conda create -y -n $VENV -c conda-forge --channel-priority $package_list
# Bail out at this point if the conda create command fails.
# Clean up zip files we've downloaded
If (-NOT ($?) ) {
    Write-Output "Failed to create conda environment.  Resolve any conflicts, then try again."
    return False
} 
# Activate the new environment
Write-Output "Activating the $VENV virtual environment"
conda activate $VENV

# Install openquake via pip
pip install openquake.engine

# This package
Write-Output "Installing gmprocess..."
pip install -e .