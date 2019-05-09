import versioneer
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize
import numpy
import glob

sourcefiles = ["gmprocess/metrics/oscillators.pyx",
               "gmprocess/metrics/cfuncs.c"]
ko_sourcefiles = ["gmprocess/smoothing/konno_ohmachi.pyx",
                  "gmprocess/smoothing/smoothing.c"]

ext_modules = [
    Extension(
        "gmprocess.metrics.oscillators",
        sourcefiles,
        libraries=["m"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-Ofast"]),
    Extension(
        "gmprocess.smoothing.konno_ohmachi",
        ko_sourcefiles,
        libraries=["m"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-Ofast"])
]

setup(
    name='gmprocess',
    description='USGS ShakeMap Ground Motion Processing Tools',
    include_package_data=True,
    author='Mike Hearne, Heather Schovanec, John, Rekoske, Eric Thompson',
    author_email='mhearne@usgs.gov, hschovanec@usgs.gov, jrekoske@usgs.gov, emthompson@usgs.gov',
    url='https://github.com/usgs/groundmotion-processing',
    version=versioneer.get_version(),
    mdclass=versioneer.get_cmdclass(),
    packages=[
        'gmprocess',
        'gmprocess.io',
        'gmprocess.io.asdf',
        'gmprocess.io.bhrc',
        'gmprocess.io.fdsn',
        'gmprocess.io.nsmn',
        'gmprocess.io.cwb',
        'gmprocess.io.dmg',
        'gmprocess.io.geonet',
        'gmprocess.io.knet',
        'gmprocess.io.cosmos',
        'gmprocess.io.smc',
        'gmprocess.io.usc',
        'gmprocess.metrics',
        'gmprocess.metrics.imt',
        'gmprocess.metrics.imc',
        'gmprocess.metrics.rotation',
        'gmprocess.metrics.combination',
        'gmprocess.metrics.transform',
        'gmprocess.metrics.reduction',
        'gmprocess.smoothing'],
    package_data={
        'gmprocess':
            glob.glob('gmprocess/data/**', recursive=True)
    },
    scripts=glob.glob('bin/*'),
    cmdclass={
        "build_ext": build_ext
    },
    ext_modules=cythonize(ext_modules)
)
