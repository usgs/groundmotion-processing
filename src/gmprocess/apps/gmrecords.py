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
import shutil
import importlib.metadata

from pathlib import Path

from gmprocess.subcommands.projects import Project
from ..subcommands.lazy_loader import LazyLoader

VERSION = importlib.metadata.version("gmprocess")

configobj = LazyLoader("configobj", globals(), "configobj")
setuptools_scm = LazyLoader("setuptools_scm", globals(), "setuptools_scm")

base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
configmod = LazyLoader("config", globals(), "gmprocess.utils.config")
const = LazyLoader("const", globals(), "gmprocess.utils.constants")
log_utils = LazyLoader("log_utils", globals(), "gmprocess.utils.logging")
projmod = LazyLoader("projmod", globals(), "gmprocess.subcommands.projects")
init = LazyLoader("init", globals(), "gmprocess.subcommands.init")
prompt = LazyLoader("prompt", globals(), "gmprocess.utils.prompt")


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
        if "CALLED_FROM_PYTEST" in os.environ:
            projects_path = const.CONFIG_PATH_TEST
        else:
            local_proj = Path.cwd() / const.PROJ_CONF_DIR
            local_proj_conf = local_proj / const.PROJ_CONF_FILE
            if local_proj.is_dir() and local_proj_conf.is_file():
                projects_path = local_proj
            else:
                projects_path = const.PROJECTS_PATH

        self.projects_path = projects_path
        self.projects_file = projects_path / const.PROJ_CONF_FILE
        self.gmprocess_version = VERSION

        self.projects_conf = None
        self.conf = None
        self.classes = {}

    def main(self, **kwargs):
        self.args = (
            argparse.Namespace(**kwargs) if kwargs else self._parse_command_line()
        )

        if self.args.subcommand is None:
            parser.print_help()
            sys.exit()
        else:
            subcmds_noinit = ["init"]
            if not self.args.subcommand in subcmds_noinit:
                self._initialize()

            subcmds_quiet = ["init", "projects", "proj"]
            if not self.args.subcommand in subcmds_quiet and not self.args.quiet:
                # Print the current project information to avoid confusion
                proj = Project.from_config(self.projects_conf, self.project_name)
                print("-" * 80)
                print(proj)
                print("-" * 80)
            # -----------------------------------------------------------------
            # This calls the init method of the subcommand that was specified
            # at the command line and hands off the GmpApp object ("self") as
            # the only argument to func.
            # -----------------------------------------------------------------
            self.args.func().main(self)

    def load_subcommands(self):
        """Load information for subcommands."""
        mod = importlib.import_module("gmprocess.subcommands")
        subcommands = {
            name: importlib.import_module(name)
            for finder, name, ispkg in pkgutil.iter_modules(
                mod.__path__, mod.__name__ + "."
            )
        }
        self.classes = {}
        for name, module in subcommands.items():
            for m in inspect.getmembers(module, inspect.isclass):
                if m[1].__module__ == name:
                    core_class = getattr(module, m[0])
                    # Check that core_class is a SubcommandModule because it is
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
                        "class": core_class,
                        "module": module,
                        "mfile": module.__file__,
                    }

    @property
    def project_name(self):
        return self.projects_conf["project"]

    @property
    def current_project(self):
        return self.projects_conf["projects"][self.project_name]

    @property
    def conf_path(self):
        return (self.projects_path / self.current_project["conf_path"]).resolve()

    @property
    def data_path(self):
        return (self.projects_path / self.current_project["data_path"]).resolve()

    def _initialize(self):
        require_config = self.args.subcommand not in ["projects", "proj"]
        self._load_config(require_config)

        log_file = self.args.log or None
        if log_file and not self.args.quiet:
            print(f"Logging output sent to: {log_file}")
        log_utils.setup_logger(self.args, log_file=log_file)
        logging.info("Logging level includes INFO.")
        logging.debug("Logging level includes DEBUG.")
        logging.info(f"PROJECTS_PATH: {self.projects_path}")

    def _load_config(self, require_config=True):
        self.projects_conf = None
        if not self.projects_file.is_file():
            if not require_config:
                return

            # If projects.conf file doesn't exist and we need one, then run the
            # initial setup.
            msg = (
                "No project config file detected. Please select a project setup option:",
                "(1) Initialize the current directory as a gmrecords project,",
                "    which will contain data and conf subdirectories.",
                "(2) Setup a project with data and conf locations that are",
                "    independent of the current directory.",
                "(3) Exit.",
            )
            print("\n".join(msg))
            response = int(input("> "))
            if response not in [1, 2, 3]:
                print("Not a valid response. Exiting.")
                sys.exit(1)
            elif response == 1:
                init.InitModule().main(self)
                self.projects_path = Path.cwd() / const.PROJ_CONF_DIR
                self.projects_file = self.projects_path / const.PROJ_CONF_FILE
            elif response == 2:
                self._initial_setup()
            else:
                sys.exit(0)

        self.projects_conf = configobj.ConfigObj(
            str(self.projects_file), encoding="utf-8"
        )
        projmod.validate_projects_config(self.projects_conf, self.projects_path)

        if "CALLED_FROM_PYTEST" in os.environ:
            conf_path = const.CONFIG_PATH_TEST
            conf_path.mkdir(exist_ok=True)
            test_conf_file = (const.DATA_DIR / const.CONFIG_FILE_TEST).resolve()
            shutil.copyfile(test_conf_file, conf_path / const.CONFIG_FILE_TEST)

        subcommands_need_conf = ["download", "assemble", "auto_shakemap"]
        if self.args.func.command_name in subcommands_need_conf:
            self.conf = configmod.get_config(config_path=self.conf_path)

    def _initial_setup(self):
        """
        Initial setup of ~/.gmprogress/projects.conf; essentially invoke
        # gmrecords projects -c
        """
        self.projects_path.mkdir(exist_ok=True)
        empty_conf = configobj.ConfigObj(encoding="utf-8")
        empty_conf.filename = self.projects_file
        projmod.create(empty_conf)

    def _parse_command_line(self):
        """Parse command line arguments."""
        # Main program parser
        description = """
        gmrecords is a program for retrieving and processing ground motion
        records, as well as exporting commonly used station and waveform
        parameters for earthquake hazard analysis.
        """
        parser = argparse.ArgumentParser(description=description)
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "-d",
            "--debug",
            action="store_true",
            help="Print all informational messages.",
        )
        group.add_argument(
            "-q", "--quiet", action="store_true", help="Print only errors."
        )
        parser.add_argument(
            "-v",
            "--version",
            action="version",
            version="%(prog)s " + VERSION,
            help="Print program version.",
        )
        parser.add_argument(
            "-l",
            "--log",
            action="store",
            type=str,
            default=None,
            help="Path to log file; if provided, loging is directed to this file.",
        )

        # Parsers for subcommands
        subparsers = parser.add_subparsers(
            title="Subcommands", dest="subcommand", metavar="<command> (<aliases>)"
        )

        # Get subcommands and their arguments
        self.load_subcommands()
        parsers = []
        for cname, cdict in self.classes.items():
            command_description = inspect.getdoc(cdict["class"])
            if hasattr(cdict["class"], "epilog"):
                epilog = cdict["class"].epilog
            else:
                epilog = None
            parsers.append(
                subparsers.add_parser(
                    cname,
                    help=command_description,
                    aliases=cdict["class"].aliases,
                    epilog=epilog,
                    formatter_class=argparse.RawDescriptionHelpFormatter,
                )
            )
            arg_list = cdict["class"].arguments
            for arg_dict in arg_list:
                targ_dict = copy.copy(arg_dict)
                # Move positional arguments to a list
                pargs = []
                if "short_flag" in arg_dict:
                    pargs.append(arg_dict["short_flag"])
                if "long_flag" in arg_dict:
                    pargs.append(arg_dict["long_flag"])
                targ_dict.pop("short_flag", None)
                targ_dict.pop("long_flag", None)
                parsers[-1].add_argument(*pargs, **targ_dict)
            parsers[-1].set_defaults(func=cdict["class"])
        return parser.parse_args()
