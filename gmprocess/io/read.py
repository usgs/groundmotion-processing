# stdlib imports
import importlib
import os.path
import logging
import pkg_resources

# third party imports
import numpy as np

# local imports
from gmprocess.utils.exception import GMProcessException


EXCLUDED = ['__pycache__']


def read_data(filename, read_format=None, **kwargs):
    """
    Read strong motion data from a file.

    Args:
        filename (str): Path to file
        read_format (str): Format of file

    Returns:
        list: Sequence of obspy.core.stream.Streams read from file
    """
    # Check if file exists
    if not os.path.exists(filename):
        raise GMProcessException('Not a file %r' % filename)
    # Get and validate format
    if read_format is None:
        read_format = _get_format(filename)
    else:
        read_format = _validate_format(filename, read_format.lower())
    # Load reader and read file
    reader = 'gmprocess.io.' + read_format + '.core'
    reader_module = importlib.import_module(reader)
    read_name = 'read_' + read_format
    read_method = getattr(reader_module, read_name)
    streams = read_method(filename, **kwargs)
    return streams


def _get_format(filename):
    """
    Get the format of the file.

    Args:
        filename (str): Path to file

    Returns:
        string: Format of file.
    """
    # Get the valid formats
    valid_formats = []
    io_directory = pkg_resources.resource_filename('gmprocess', 'io')
    # Create valid list
    for module in os.listdir(io_directory):
        if module.find('.') < 0 and module not in EXCLUDED:
            valid_formats += [module]
    # Test each format
    formats = []
    for valid_format in valid_formats:
        # Create the module and function name from the request
        reader = 'gmprocess.io.' + valid_format + '.core'
        reader_module = importlib.import_module(reader)
        is_name = 'is_' + valid_format
        is_method = getattr(reader_module, is_name)
        if is_method(filename):
            formats += [valid_format]
    # Return the format
    formats = np.asarray(formats)
    if len(formats) == 1:
        return formats[0]
    elif len(formats) == 2 and 'gmobspy' in formats:
        return formats[formats != 'gmobspy'][0]
    elif len(formats) == 0:
        raise GMProcessException('No format found for file %r.' % filename)
    else:
        raise GMProcessException(
            'Multiple formats passing: %r. Please retry file %r '
            'with a specified format.' % (formats.tolist(), filename))


def _validate_format(filename, read_format):
    """
    Check if the specified format is valid. If not, get format.

    Args:
        filename (str): Path to file
        read_format (str): Format of file

    Returns:
        string: Format of file.
    """
    # Get the valid formats
    valid_formats = []
    home = os.path.dirname(os.path.abspath(__file__))
    io_directory = os.path.abspath(os.path.join(home, '..', 'io'))
    # Create valid list
    for module in os.listdir(io_directory):
        if module.find('.') < 0 and module not in EXCLUDED:
            valid_formats += [module]
    # Check for a valid format
    if read_format in valid_formats:
        reader = 'gmprocess.io.' + read_format + '.core'
        reader_module = importlib.import_module(reader)
        is_name = 'is_' + read_format
        is_method = getattr(reader_module, is_name)
    else:
        logging.warning('Not a supported format %r. '
                        'Attempting to find a supported format.' % read_format)
        return _get_format(filename)
    # Check that the format passes tests
    if is_method(filename):
        return read_format
    else:
        logging.warning('File did not match specified format. '
                        'Attempting to find a supported format.')
        return _get_format(filename)
