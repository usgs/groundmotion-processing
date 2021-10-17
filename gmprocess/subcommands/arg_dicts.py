#!/usr/bin/env python
# -*- coding: utf-8 -*-

ARG_DICTS = {
    'label': {
        'short_flag': '-l',
        'long_flag': '--label',
        'help': ('Processing label. If None (default) then we will disregard '
                 'the unprocessed label, and if there is only one remaining '
                 'label then we will use it. If there are multiple remaining '
                 'labels then we will prmpt you to select one.'),
        'type': str,
        'default': None,
    },
    'eventid': {
        'short_flag': '-e',
        'long_flag': '--eventid',
        'help': ('Comcat event ID. If None (default) all events in '
                 'project data directory will be used.'),
        'type': str,
        'default': None,
        'nargs': '+'
    },
    'overwrite': {
        'short_flag': '-o',
        'long_flag': '--overwrite',
        'help': 'Overwrite results if they exist.',
        'default': False,
        'action': 'store_true'
    },
    'output_format': {
        'short_flag': '-f',
        'long_flag': '--output-format',
        'help': 'Output file format.',
        'type': str,
        'default': 'csv',
        'choices': ['excel', 'csv'],
        'metavar': 'FORMAT'
    },
    'num_processes': {
        'short_flag': '-n',
        'long_flag': '--num-processes',
        'help': 'Number of parallel processes to run over events.',
        'type': int,
        'default': 0,
        'metavar': 'n'
    },
    'textfile': {
        'short_flag': '-t',
        'long_flag': '--textfile',
        'help': (
            'Text file containing lines of ComCat Event IDs or event '
            'information (ID TIME LAT LON DEPTH MAG).'),
        'type': str,
        'default': None
    }
}
