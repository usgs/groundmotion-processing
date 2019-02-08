import os
import versioneer
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize
import numpy
import glob

sourcefiles = ["gmprocess/metrics/oscillators.pyx",
               "gmprocess/metrics/cfuncs.c"]

ext_modules = [Extension("gmprocess.metrics.oscillators",
                         sourcefiles,
                         libraries=["m"],
                         include_dirs=[numpy.get_include()],
                         extra_compile_args=["-Ofast"])]

setup(name='gmprocess',
      description='USGS ShakeMap Ground Motion Processing Tools',
      include_package_data=True,
      author='Mike Hearne',
      author_email='mhearne@usgs.gov',
      url='',
      version=versioneer.get_version(),
      mdclass=versioneer.get_cmdclass(),
      packages=['gmprocess',
                'gmprocess.io',
                'gmprocess.io.cwb',
                'gmprocess.io.dmg',
                'gmprocess.io.geonet',
                'gmprocess.io.knet',
                'gmprocess.io.cosmos',
                'gmprocess.io.smc',
                'gmprocess.io.obspy',
                'gmprocess.io.usc',
                'gmprocess.metrics',
                'gmprocess.metrics.imt',
                'gmprocess.metrics.imc'],
      package_data={'gmprocess': glob.glob('gmprocess/io/*.csv') +
                    glob.glob('tests/data/*/*'),
                    'metrics': glob.glob('gmprocess/io/*.csv') +
                    glob.glob('tests/data/*/*')
                    },
      scripts=['bin/fdsnfetch',
               'bin/ftpfetch',
               'bin/gm2table',
               'bin/gmconvert',
               'bin/gminfo',
               'bin/ingvfetch'],
      cmdclass={"build_ext": build_ext},
      ext_modules=cythonize(ext_modules)
      )
