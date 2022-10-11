#!/usr/bin/env python
# -*- coding: utf-8 -*-


def get_rawdir(event_dir):
    """Find or create raw directory if necessary.

    Args:
        event_dir (str):
            Directory where raw directory will be found or created.
    """
    rawdir = event_dir / "raw"
    rawdir.mkdir(exist_ok=True)
    return rawdir
