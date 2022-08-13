#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Helper functions to organize/import processing steps.
"""

import importlib
import inspect
import os
from pathlib import Path


def ProcessingStep(func):
    """A decorator to mark processing step functions."""
    func.is_processing_step = True
    return func


def collect_processing_steps():
    """Collect processing steps into a dictionary.

    Returns:
        dict: keys are the function name, values are the module object.
    """
    step_dict = {}
    root = Path(__file__).parent
    module_files = root.glob("**/*.py")
    for mf in module_files:
        mod_str = str(mf)
        if mod_str.find("__") >= 0:
            continue
        if mod_str.endswith("processing.py") or mod_str.endswith("processing_step.py"):
            continue
        module_name = __path_to_module(mod_str)
        module = importlib.import_module(module_name)
        for name, obj in inspect.getmembers(module):
            if hasattr(obj, "is_processing_step"):
                step_dict[name] = obj
    return step_dict


def __path_to_module(path):
    mod_name = path[path.rfind("gmprocess") :].replace(".py", "")
    mod_name = mod_name.replace(os.path.sep, ".")
    return mod_name
