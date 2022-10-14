#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path


def get_rawdir(event_dir):
    """Find or create raw directory if necessary.

    Args:
        event_dir (str):
            Directory where raw directory will be found or created.
    """
    event_dir = Path(event_dir)
    rawdir = event_dir / "raw"
    rawdir.mkdir(exist_ok=True)
    return rawdir
