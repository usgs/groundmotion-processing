# -*- coding: utf-8 -*-

import os
import glob
import numpy

from distutils.sysconfig import get_config_vars as default_get_config_vars

# Modification of method for removing pthread described here:
# https://stackoverflow.com/questions/57046796/how-to-remove-pthread-compiler-flag-from-cython-setup-file
def remove_sysroot(x):
    # if type(x) is str:
    #    arg_list = x.split()
    #    new_arg_list = [a for a in arg_list if a != "-Wl,--sysroot=/"]
    #    x = " ".join(new_arg_list)
    return x


def my_get_config_vars(*args):
    result = default_get_config_vars(*args)
    # sometimes result is a list and sometimes a dict:
    if type(result) is list:
        return [remove_sysroot(x) for x in result]
    elif type(result) is dict:
        return {k: remove_sysroot(x) for k, x in result.items()}
    else:
        raise Exception("cannot handle type" + type(result))


import distutils.sysconfig as dsc
from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext

dsc.get_config_vars = my_get_config_vars

osc_sourcefiles = ["gmprocess/metrics/oscillators.pyx", "gmprocess/metrics/cfuncs.c"]
ko_sourcefiles = [
    "gmprocess/waveform_processing/smoothing/konno_ohmachi.pyx",
    "gmprocess/waveform_processing/smoothing/smoothing.c",
]

libraries = []
if os.name == "posix":
    libraries.append("m")
    libraries.append("omp")

ext_modules = [
    Extension(
        "gmprocess.metrics.oscillators",
        osc_sourcefiles,
        libraries=libraries,
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-O2", "-Xpreprocessor", "-fopenmp"],
        extra_link_args=["-Xpreprocessor", "-fopenmp"],
    ),
    Extension(
        "gmprocess.waveform_processing.smoothing.konno_ohmachi",
        ko_sourcefiles,
        libraries=libraries,
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-O2", "-Xpreprocessor", "-fopenmp"],
        extra_link_args=["-Xpreprocessor", "-fopenmp"],
    ),
]


setup(
    name="gmprocess",
    description="USGS Automated Ground Motion Processing Software",
    include_package_data=True,
    author=(
        "Mike Hearne, Eric Thompson, "
        "Heather Schovanec, John Rekoske, "
        "Brad Aagaard, Bruce Worden"
    ),
    author_email=(
        "mhearne@usgs.gov, emthompson@usgs.gov, "
        "hschovanec@usgs.gov, jrekoske@usgs.gov, "
        "baagaard@usgs.gov, cbworden@contractor.usgs.gov"
    ),
    url="https://github.com/usgs/groundmotion-processing",
    packages=[
        "gmprocess",
        "gmprocess.apps",
        "gmprocess.bin",
        "gmprocess.subcommands",
        "gmprocess.core",
        "gmprocess.io",
        "gmprocess.io.asdf",
        "gmprocess.io.bhrc",
        "gmprocess.io.esm",
        "gmprocess.io.obspy",
        "gmprocess.io.nsmn",
        "gmprocess.io.cwb",
        "gmprocess.io.dmg",
        "gmprocess.io.geonet",
        "gmprocess.io.knet",
        "gmprocess.io.cosmos",
        "gmprocess.io.renadic",
        "gmprocess.io.smc",
        "gmprocess.io.unam",
        "gmprocess.io.usc",
        "gmprocess.metrics",
        "gmprocess.metrics.imt",
        "gmprocess.metrics.imc",
        "gmprocess.metrics.rotation",
        "gmprocess.metrics.combination",
        "gmprocess.metrics.transform",
        "gmprocess.metrics.reduction",
        "gmprocess.utils",
        "gmprocess.waveform_processing",
        "gmprocess.waveform_processing.smoothing",
    ],
    package_data={"gmprocess": glob.glob("gmprocess/data/**", recursive=True)},
    entry_points={
        "console_scripts": [
            "gmconvert = gmprocess.bin.gmconvert:main",
            "gminfo = gmprocess.bin.gminfo:main",
            "gmrecords = gmprocess.bin.gmrecords:main",
            "gmworkspace = gmprocess.bin.gmworkspace:main",
            "list_metrics = gmprocess.bin.list_metrics:main",
        ]
    },
    cmdclass={"build_ext": build_ext},
    ext_modules=cythonize(ext_modules),
    zip_safe=False,
)
