#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


def get_rawdir(event_dir):
    """Find or create raw directory if necessary.

    Args:
        event_dir (str):
            Directory where raw directory will be found or created.
    """
    rawdir = os.path.join(event_dir, "raw")
    if not os.path.exists(rawdir):
        os.makedirs(rawdir)
    return rawdir
