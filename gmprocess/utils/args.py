#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools_scm import get_version


def add_shared_args(parser):
    """Method for arguments shared across all programs.

    parser:
        An argparse object.

    Returns:
        An argparse object.

    """
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-d', '--debug', action='store_true',
        help='Print all informational messages.')
    group.add_argument(
        '-q', '--quiet', action='store_true',
        help='Print only errors.')
    __version__ = get_version(
        root=os.path.join(os.pardir, os.pardir),
        relative_to=__file__)
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s ' + __version__,
                        help='Print program version.')
    return parser
