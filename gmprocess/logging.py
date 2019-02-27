import logging
import logging.config


def setup_logger(args=None):
    """Setup the logger options.

    Args:
        args (argparse): Must contain logging options in
            gmprocess.args.add_shared_args.

    """

    fmt = ('%(levelname)s %(asctime)s | '
           '%(module)s.%(funcName)s: %(message)s')
    datefmt = '%Y-%m-%d %H:%M:%S'
    # create a console handler, with verbosity setting chosen by user
    if args is not None:
        if args.debug:
            level = logging.DEBUG
        elif args.quiet:
            level = logging.ERROR
        else:  # default interactive
            level = logging.INFO
    else:
        level = logging.DEBUG

    logdict = {
        'version': 1,
        'formatters': {
            'standard': {
                'format': fmt,
                'datefmt': datefmt
            }
        },
        'handlers': {
            'stream': {
                'level': level,
                'formatter': 'standard',
                'class': 'logging.StreamHandler'
            }
        },
        'loggers': {
            '': {
                'handlers': ['stream'],
                'level': level,
                'propagate': True
            }
        }
    }

    logging.config.dictConfig(logdict)

    # Have the logger capture anything from the 'warnings' package,
    # which many libraries use.
    logging.captureWarnings(True)
