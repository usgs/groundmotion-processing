import importlib
import inspect
import os
import logging


EXCLUDED_MODULES = ['__init__.py', 'imt.py', 'imc.py']
BASE = os.path.dirname(os.path.abspath(__file__))


def gather_pgms():
    imt_directory = os.path.join(BASE, 'metrics_controller_imt')
    imc_directory = imt_directory.replace('metrics_controller_imt', 'metrics_controller_imc')
    # Create list
    imt_classes = []
    imc_classes = []
    for imt_file in os.listdir(imt_directory):
        if imt_file.endswith(".py") and imt_file not in EXCLUDED_MODULES:
            imt_file = imt_file[0:-3]
            imt_classes += [imt_file]
    for imc_file in os.listdir(imc_directory):
        if imc_file.endswith(".py") and imc_file not in EXCLUDED_MODULES:
            imc_file = imc_file[0:-3]
            imc_classes += [imc_file]
    return imt_classes, imc_classes


def get_pgm_classes(im_type):
    """
    Create a dictionary of classname:class to be used in main().

    Returns:
        dictionary: Dictionary of modules.
    """
    # Get list of available modules (excluding base and __init__)
    modules = _get_pgm_modules(im_type)
    # Put imported modules into a dictionary
    pgm_modules = {}
    for modname in modules:
        mod = importlib.import_module(modname)
        cm = {
            mod.__name__: mod
        }
        pgm_modules.update(cm)
    # Put imported classes into a dictionary
    classes = {}
    for name, module in pgm_modules.items():
        for m in inspect.getmembers(module, inspect.isfunction):
            if m[1].__module__ == name:
                if not m[0].startswith('_'):
                    core_class = getattr(module, m[0])
                    classes[core_class.__name__] = core_class
    ordered_classes = {}
    keys = sorted(classes.keys())
    for k in keys:
        ordered_classes[k] = classes[k]
    return ordered_classes


def group_imcs(imcs):
    imc_dict = {}
    for imc in imcs:
        imc = imc.lower()
        if imc.startswith('rotd'):
            try:
                if 'rotd' not in imc_dict:
                    imc_dict['rotd'] = []
                imc_dict['rotd'] += [float(imc[4:])]
            except Exception:
                logging.warning('Invalid percentile for RotD: %r' % imc)
        elif imc.startswith('roti'):
            try:
                if 'roti' not in imc_dict:
                    imc_dict['roti'] = []
                imc_dict['roti'] += [float(imc[4:])]
            except Exception:
                logging.warning('Invalid percentile for RotI: %r' % imc)
        elif imc.startswith('gmrotd'):
            try:
                if 'gmrotd' not in imc_dict:
                    imc_dict['gmrotd'] = []
                imc_dict['gmrotd'] += [float(imc[6:])]
            except Exception:
                logging.warning('Invalid percentile for GMRotD: %r' % imc)
        elif imc.startswith('gmroti'):
            try:
                if 'gmroti' not in imc_dict:
                    imc_dict['gmroti'] = []
                imc_dict['gmroti'] += [float(imc[6:])]
            except Exception:
                logging.warning('Invalid percentile for GMRotI: %r' % imc)
        else:
            imc_dict[imc] = ''
    return imc_dict


def _get_pgm_modules(im_type):
    """
    Internal method to get all pgm modules.

    Returns:
        list: List of pgm modules.
    """
    # Get path
    home = os.path.dirname(os.path.abspath(__file__))
    pgm_directory = os.path.abspath(
        os.path.join(home, '..', 'metrics', im_type))
    path = 'gmprocess.metrics.' + im_type + '.'
    # Create list
    pgm_modules = []
    for file in os.listdir(pgm_directory):
        if file.endswith(".py") and file not in EXCLUDED_MODULES:
            file = file[0:-3]
            pgm_modules += [path + file]
    return pgm_modules
