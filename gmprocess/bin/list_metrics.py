#!/usr/bin/env python

import importlib
import inspect
import os.path

import pkg_resources
import pandas as pd

from gmprocess.metrics.gather import gather_pgms
from gmprocess.metrics.imc.imc import IMC
from gmprocess.metrics.imt.imt import IMT


def get_class(imc, ctype):
    """Return class (not instance) corresponding to imc string.
    """
    if ctype == 'imt':
        compclass = IMT
    elif ctype == 'imc':
        compclass = IMC
    datapath = os.path.join('metrics', ctype)
    imc_directory = pkg_resources.resource_filename('gmprocess', datapath)
    modfile = os.path.join(imc_directory, imc + '.py')
    if not os.path.isfile(modfile):
        return None
    modname = modfile[modfile.rfind('gmprocess'):].replace('.py', '')
    modname = modname.replace(os.path.sep, '.')
    mod = importlib.import_module(modname)
    tclass = None
    for name, obj in inspect.getmembers(mod):
        if name == ctype.upper():
            continue
        if inspect.isclass(obj) and issubclass(obj, compclass):
            tclass = obj
            break

    return tclass


def get_combinations():
    imts, imcs = gather_pgms()
    dataframe = pd.DataFrame(columns=imts + ['imc'])
    checks = ['Y'] * len(imts)
    for imc in imcs:
        imc_class = get_class(imc, 'imc')
        invalid_imts = imc_class._invalid_imts
        row = dict(zip(imts, checks))
        for iimt in invalid_imts:
            row[iimt.lower()] = 'N'
        row['imc'] = imc
        dataframe = dataframe.append(row, ignore_index=True)

    dataframe = dataframe.set_index('imc')
    return dataframe


def main():
    helpstr = '''
    Table of supported IMC/IMT combinations is below.

    Notes:

    The "channels" IMC will result in three IMC channels
    called "H1", "H2", and "Z".

    The "gmrotd" and "rotd" IMCs will need to be specified as "gmrotd50"
    for the Geometric Mean 50th percentile, rotd100 for the 100th percentile,
    and so forth.
    '''
    comboframe = get_combinations()
    print(helpstr)
    print(comboframe)


if __name__ == '__main__':
    main()
