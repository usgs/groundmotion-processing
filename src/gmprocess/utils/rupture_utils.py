#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path

from gmprocess.utils.constants import RUPTURE_FILE


def get_rupture_file(event_dir):
    """Get the path to the rupture file, or None if there is not rupture file.

    Args:
        event_dir (str):
            Event directory.

    Returns:
        str: Path to the rupture file. Returns None if no rupture file exists.
    """
    event_dir = Path(event_dir)
    rupture_file = event_dir / RUPTURE_FILE
    if not rupture_file.is_file():
        rupture_file = None
    return rupture_file
