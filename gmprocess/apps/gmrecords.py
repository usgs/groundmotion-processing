#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import copy
import importlib
import pkgutil
import inspect
import argparse
import logging

from gmprocess.subcommands.lazy_loader import LazyLoader
configobj = LazyLoader('configobj', globals(), 'configobj')
setuptools_scm = LazyLoader('setuptools_scm', globals(), 'setuptools_scm')

base = LazyLoader('base', globals(), 'gmprocess.subcommands.base')
config = LazyLoader('config', globals(), 'gmprocess.utils.config')
const = LazyLoader('const', globals(), 'gmprocess.utils.constants')
log_utils = LazyLoader('log_utils', globals(), 'gmprocess.utils.logging')
projmod = LazyLoader('projmod', globals(), 'gmprocess.subcommands.projects')
init = LazyLoader('init', globals(), 'gmprocess.subcommands.init')


VERSION = setuptools_scm.get_version(
    root=os.path.join(os.pardir, os.pardir),
    relative_to=__file__)


class GMrecordsApp(object):
    """Main driver app for gmrpocess command-line interface.

    This is meant to replace the `gmprocess` program.

    To limit the number of paths specified as arguments, this app relies on
    some config options associated with "projects". Project information is
    saved in `.gmprocess/projects.conf`, either in the user's home directory
    for "system" level projects, or in a specific directory to allow for
    directory-specific projects.

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

    def __init__(self):
        # Try not to let tests interfere with actual system:
        if os.getenv('CALLED_FROM_PYTEST') is None:
            # Not called from pytest
            local_proj = os.path.join(os.getcwd(), const.PROJ_CONF_DIR)
            local_proj_conf = os.path.join(local_proj, 'projects.conf')
            if os.path.isdir(local_proj) and os.path.isfile(local_proj_conf):
                PROJECTS_PATH = local_proj
            else:
                PROJECTS_PATH = const.PROJECTS_PATH
        else:
            PROJECTS_PATH = const.PROJECTS_PATH_TEST

        self.PROJECTS_PATH = PROJECTS_PATH
        self.PROJECTS_FILE = os.path.join(PROJECTS_PATH, 'projects.conf')

        self._parse_command_line()
        self._load_config()
        self.gmprocess_version = VERSION

        log_file = None
        if self.args.log:
            log_file = os.path.join(self.data_path, 'log.txt')
            print('Logging output sent to: %s' % log_file)

        log_utils.setup_logger(self.args, log_file=log_file)
        logging.info('Logging level includes INFO.')
        logging.debug('Logging level includes DEBUG.')
        logging.info('PROJECTS_PATH: %s' % PROJECTS_PATH)

    def main(self):
        if self.args.subcommand is None:
            self.parser.print_help()
        else:
            exclude_subcommands = ['projects', 'proj', 'init']
            if self.args.subcommand not in exclude_subcommands:
                # Print the current project information to try to avoid
                # confusion
                selected_project = self.projects_conf['project']
                proj = projmod.Project(
                    selected_project,
                    self.projects_conf['projects'][selected_project],
                    self.projects_conf.filename
                )
                print('-' * 80)
                print(proj)
                print('-' * 80)
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
            print('No project config file detected.')
            print('Please select a project setup option:')
            print('(1) Initialize the current directory as a gmrecords')
            print('    project, which will contain data and conf')
            print('    subdirectories.')
            print('(2) Setup a project with data and conf locations that')
            print('    are independent of the current directory.')
            response = int(input('> '))
            if response not in [1, 2]:
                print('Not a valid response. Exiting.')
                sys.exit(0)
            elif response == 1:
                init.InitModule().main(self)
                sys.exit(0)
            else:
                self._initial_setup()

        self.projects_conf = configobj.ConfigObj(
            self.PROJECTS_FILE, encoding='utf-8')
        self.project = self.projects_conf['project']
        self.current_project = self.projects_conf['projects'][self.project]
        self.conf_path = os.path.join(
            os.path.abspath(os.path.join(self.PROJECTS_FILE, os.pardir)),
            self.current_project['conf_path'])
        self.data_path = os.path.join(
            os.path.abspath(os.path.join(self.PROJECTS_FILE, os.pardir)),
            self.current_project['data_path'])
        if os.getenv('CALLED_FROM_PYTEST') is not None:
            self.conf_path = const.PROJECTS_PATH_TEST
        self.conf_file = os.path.join(self.conf_path, 'config.yml')
        if not os.path.isfile(self.conf_file):
            print('Config file does not exist: %s' % self.conf_file)
            print('Exiting.')
            sys.exit(1)
        self.conf = config.get_config(self.conf_file)

    def _initial_setup(self):
        """
        Initial setup of ~/.gmprogress/projects.conf; essentially invoke
        # gmrecords projects -c
        """
        if not os.path.isdir(self.PROJECTS_PATH):
            os.mkdir(self.PROJECTS_PATH)
        empty_conf = configobj.ConfigObj(encoding='utf-8')
        empty_conf.filename = self.PROJECTS_FILE
        projmod.create(empty_conf)
        # Need to exit here because if gmp projects -c is called when there is
        # no prior setup, the user would otherwise be forced to setup two
        # projects.
        sys.exit(0)

    def _parse_command_line(self):
        """Parse command line arguments.
        """
        # Main program parser
        description = """
        gmrecords is a program for retrieving and processing ground motion
        records, as well as exporting commonly used station and waveform
        parameters for earthquake hazard analysis.
        """
        self.parser = argparse.ArgumentParser(description=description)
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument(
            '-d', '--debug', action='store_true',
            help='Print all informational messages.')
        group.add_argument(
            '-q', '--quiet', action='store_true',
            help='Print only errors.')
        self.parser.add_argument(
            '-v', '--version', action='version',
            version='%(prog)s ' + VERSION,
            help='Print program version.')
        self.parser.add_argument(
            '-l', '--log', action='store_true', default=False,
            help='Log all output to a file in the project data directory.')

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
                    if not issubclass(core_class, base.SubcommandModule):
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
