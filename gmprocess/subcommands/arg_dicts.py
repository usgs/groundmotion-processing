ARG_DICTS = {
    'label': {
        'short_flag': '-l',
        'long_flag': '--label',
        'help': ('Processing label. If None (default) then we will use '
                     'the unprocessed lable if there is only one, and prompt '
                     'you to select one otherwise.'),
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
        'choices': ['excel', 'csv']
    },
    'num_processes': {
        'short_flag': '-n',
        'long_flag': '--num-processes',
        'help': 'Number of parallel processes to run over events.',
        'type': int,
        'default': 0,
    }
}
