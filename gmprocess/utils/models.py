#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pkg_resources
from importlib import import_module
from ruamel.yaml import YAML

from gmprocess.utils.constants import MODULE_FILE


def load_model(model):
    """
    Loads a ground shaking intensity model from the modules file.

    Args:
        model (str):
            The shorthand string for the model, defined in the modules file.
    Returns:
        The openquake ground shaking intensity model object.
    """
    mod_file = pkg_resources.resource_filename(
        'gmprocess', os.path.join('data', MODULE_FILE))
    with open(mod_file, 'r', encoding='utf-8') as f:
        yaml = YAML()
        yaml.preserve_quotes = True
        mods = yaml.load(f)

    # Import module
    cname, mpath = mods['modules'][model]
    dmodel = getattr(import_module(mpath), cname)()
    return dmodel
