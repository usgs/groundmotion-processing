import os
import sys
import copy
import importlib
import pkgutil
import inspect
import argparse
from argparse import RawTextHelpFormatter
import logging

from configobj import ConfigObj
import logging
from setuptools_scm import get_version

from gmprocess.utils.config import get_config
from gmprocess.utils.logging import setup_logger
from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.projects import create
from gmprocess.utils.prompt import set_project_paths, get_default_project_paths


class GmpApp(object):
    """Main driver app for gmrpocess command-line interface.

    This is meant to replace the `gmrpocess` program.

    To limit the number of paths specified as arguments, this app relies on
    some config options associated with "projects". Project information is
    saved in `~/.gmp/projects.conf`.

    GmpApp makes use subcommands that are specified in the
    gmprocess.subcommands package.

    Projects can be set up, listed, and modified with the `project` subcommand.

    Projects contain:
        - Path to the data directory. Note that this is equivalent to the
          '--output-directory' path in gmprocess.
        - Path to the conf directory, where config.yml is located.
            * Note: The plan is for this directory to holds multiple conf
              files so that we can split up the current content to make it
              easier to deal with.
    """

    PROJECTS_PATH = os.path.join(os.path.expanduser('~'), '.gmp')
    PROJECTS_FILE = os.path.join(PROJECTS_PATH, 'projects.conf')

    def __init__(self):
        self._load_config()
        self._parse_command_line()
        setup_logger(self.args)
        logging.info('Logging level includes INFO.')
        logging.debug('Logging level includes DEBUG.')

    def main(self):
        # Putting this here because `execute` needs to happen after logging
        # is setup.
        if self.args.subcommand is None:
            self.parser.print_help()
        else:
            # -----------------------------------------------------------------
            # This calls the init method of the subcommand that was specified
            # at the command line and hands off the GmpApp object ("self") as
            # the only argument to func.
            # -----------------------------------------------------------------
            self.args.func().main(self)

    def _load_config(self):
        if not os.path.isfile(self.PROJECTS_FILE):
            # If projects.conf file doesn't exist then we need to run the
            # initial setup.
            print('No projects config file detected. Running initial setup...')
            self._initial_setup()

        self.projects_conf = ConfigObj(self.PROJECTS_FILE)
        self.project = self.projects_conf['project']
        self.current_project = self.projects_conf['projects'][self.project]
        self.conf_path = self.current_project['conf_path']
        self.data_path = self.current_project['data_path']
        self.conf_file = os.path.join(self.conf_path, 'config.yml')
        if not os.path.isfile(self.conf_file):
            print('Config file does not exist: %s' % self.conf_file)
            print('Exiting.')
            sys.exit(1)
        self.conf = get_config(self.conf_file)

    def _initial_setup(self):
        """
        Initial setup of ~/.gmp/projects.conf; essentially invoke
        # gmp projects -c <project>
        """
        if not os.path.isdir(self.PROJECTS_PATH):
            os.mkdir(self.PROJECTS_PATH)
        project_name = input('Please enter a project title:')
        empty_conf = ConfigObj()
        empty_conf.filename = self.PROJECTS_FILE
        create(empty_conf, project_name)

    def _parse_command_line(self):
        """Parse command line arguments.
        """
        # Main program parser
        description = """
        gmp is a program for retrieving and processing ground motion records,
        as well as exporting commonly used station and waveform parameters for
        earthquake hazard analysis.
        """
        self.parser = argparse.ArgumentParser(description=description)
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument(
            '-d', '--debug', action='store_true',
            help='Print all informational messages.')
        group.add_argument(
            '-q', '--quiet', action='store_true',
            help='Print only errors.')
        __version__ = get_version(
            root=os.path.join(os.pardir, os.pardir),
            relative_to=__file__)
        self.parser.add_argument(
            '-v', '--version', action='version',
            version='%(prog)s ' + __version__,
            help='Print program version.')

        # Parsers for subcommands
        subparsers = self.parser.add_subparsers(
            title='Subcommands', dest="subcommand",
            metavar="<command> (<aliases>)")

        # Get subcommands and their arguments
        mod = importlib.import_module('gmprocess.subcommands')
        subcommands = {
            name: importlib.import_module(name)
            for finder, name, ispkg
            in pkgutil.iter_modules(mod.__path__, mod.__name__ + ".")
        }
        self.classes = {}
        for name, module in subcommands.items():
            for m in inspect.getmembers(module, inspect.isclass):
                if m[1].__module__ == name:
                    core_class = getattr(module, m[0])
                    # Check that core_class is a SubcommandModule becuase it is
                    # possible that other classes will be defined in the
                    # module.
                    if not issubclass(core_class, SubcommandModule):
                        continue
                    # Check that command_name is a string because we want to
                    # skip the SubcommandModule base class.
                    if not isinstance(core_class.command_name, str):
                        continue
                    cmd = core_class.command_name
                    if not cmd:
                        continue
                    self.classes[cmd] = {
                        'class': core_class,
                        'module': module,
                        'mfile': module.__file__
                    }
        parsers = []
        for cname, cdict in self.classes.items():
            command_description = inspect.getdoc(cdict['class'])
            parsers.append(
                subparsers.add_parser(
                    cname,
                    help=command_description,
                    aliases=cdict['class'].aliases
                )
            )
            arg_list = cdict['class'].arguments
            for arg_dict in arg_list:
                targ_dict = copy.copy(arg_dict)
                # Move positional arguments to a list
                pargs = []
                if 'short_flag' in arg_dict:
                    pargs.append(arg_dict['short_flag'])
                if 'long_flag' in arg_dict:
                    pargs.append(arg_dict['long_flag'])
                targ_dict.pop('short_flag', None)
                targ_dict.pop('long_flag', None)
                parsers[-1].add_argument(*pargs, **targ_dict)
            parsers[-1].set_defaults(func=cdict['class'])
        self.args = self.parser.parse_args()
