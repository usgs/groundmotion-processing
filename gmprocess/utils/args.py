#!/usr/bin/env python
import versioneer


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
    __version__ = versioneer.get_version()
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s ' + __version__,
                        help='Print program version.')
    return parser
