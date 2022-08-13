# -*- coding: utf-8 -*-

import os
import numpy

from setuptools import Extension, setup
from Cython.Build import cythonize

osc_sourcefiles = ["gmprocess/metrics/oscillators.pyx", "gmprocess/metrics/cfuncs.c"]
ko_sourcefiles = [
    "gmprocess/waveform_processing/smoothing/konno_ohmachi.pyx",
    "gmprocess/waveform_processing/smoothing/smoothing.c",
]
auto_fchp_sourcefiles = ["gmprocess/waveform_processing/auto_fchp.pyx"]

libraries = []
if os.name == "posix":
    libraries.append("m")
    # libraries.append("omp")

ext_modules = [
    Extension(
        name="gmprocess.metrics.oscillators",
        sources = osc_sourcefiles,
        libraries=libraries,
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-O1"],
    ),
    Extension(
        name="gmprocess.waveform_processing.smoothing.konno_ohmachi",
        sources = ko_sourcefiles,
        libraries=libraries,
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-O2"],
    ),
    Extension(
        name="gmprocess.waveform_processing.auto_fchp",
        sources = auto_fchp_sourcefiles,
        libraries=libraries,
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-O2"],
    ),
]


setup(
    # packages=["metrics"],
    package_dir={'': 'gmprocess'},
    ext_modules=cythonize(ext_modules),
)
