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
        include_dirs=[numpy.get_include()]),
    Extension(
        "gmprocess.smoothing.konno_ohmachi",
        ko_sourcefiles,
        libraries=["m"],
        include_dirs=[numpy.get_include()])
]

setup(
    name='gmprocess',
    description='USGS Automated Ground Motion Processing Software',
    include_package_data=True,
    author=('Mike Hearne, Eric Thompson, '
            'Heather Schovanec, John Rekoske, '
            'Brad Aagaard, Bruce Worden'),
    author_email=('mhearne@usgs.gov, emthompson@usgs.gov, '
                  'hschovanec@usgs.gov, jrekoske@usgs.gov, '
                  'baagaard@usgs.gov, cbworden@contractor.usgs.gov'),
    url='https://github.com/usgs/groundmotion-processing',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    mdclass=versioneer.get_cmdclass(),
    packages=[
        'gmprocess',
        'gmprocess.bin',
        'gmprocess.io',
        'gmprocess.io.asdf',
        'gmprocess.io.bhrc',
        'gmprocess.io.esm',
        'gmprocess.io.obspy',
        'gmprocess.io.nsmn',
        'gmprocess.io.cwb',
        'gmprocess.io.dmg',
        'gmprocess.io.geonet',
        'gmprocess.io.knet',
        'gmprocess.io.cosmos',
        'gmprocess.io.renadic',
        'gmprocess.io.smc',
        'gmprocess.io.unam',
        'gmprocess.io.usc',
        'gmprocess.metrics',
        'gmprocess.metrics.imt',
        'gmprocess.metrics.imc',
        'gmprocess.metrics.rotation',
        'gmprocess.metrics.combination',
        'gmprocess.metrics.transform',
        'gmprocess.metrics.reduction',
        'gmprocess.smoothing'
    ],
    package_data={
        'gmprocess':
            glob.glob('gmprocess/data/**', recursive=True)
    },
    entry_points={
        'console_scripts': [
            'gmconvert = gmprocess.bin.gmconvert:main',
            'gminfo = gmprocess.bin.gminfo:main',
            'gmprocess = gmprocess.bin.gmprocess:main',
            'gmsetup = gmprocess.bin.gmsetup:main',
            'gmworkspace = gmprocess.bin.gmworkspace:main',
            'list_metrics = gmprocess.bin.list_metrics:main'
        ]
    },
    ext_modules=cythonize(ext_modules)
)
