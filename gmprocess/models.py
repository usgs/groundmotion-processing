import os
import yaml
import pkg_resources
from importlib import import_module

from gmprocess.constants import MODULE_FILE


def load_model(model):
    mod_file = pkg_resources.resource_filename(
        'gmprocess', os.path.join('data', MODULE_FILE))
    with open(mod_file, 'r') as f:
        mods = yaml.load(f, Loader=yaml.FullLoader)

    # Import module
    cname, mpath = mods['modules'][model]
    dmodel = getattr(import_module(mpath), cname)()
    return dmodel
