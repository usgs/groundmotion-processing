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
        # Try not to let tests interfere with actual system:
        if os.getenv("CALLED_FROM_PYTEST") is None:
            # Not called from pytest
            local_proj = os.path.join(os.getcwd(), const.PROJ_CONF_DIR)
            local_proj_conf = os.path.join(local_proj, "projects.conf")
            if os.path.isdir(local_proj) and os.path.isfile(local_proj_conf):
                PROJECTS_PATH = local_proj
            else:
                PROJECTS_PATH = const.PROJECTS_PATH
        else:
            PROJECTS_PATH = const.CONFIG_PATH_TEST

        self.PROJECTS_PATH = PROJECTS_PATH
        self.PROJECTS_FILE = os.path.join(PROJECTS_PATH, "projects.conf")
        self.gmprocess_version = VERSION

    def main(self, **kwargs):
        self.args = (
            argparse.Namespace(**kwargs) if kwargs else self._parse_command_line()
        )

        if self.args.subcommand is None:
            self.parser.print_help()
            sys.exit()
        else:
            self._initialize()
            exclude_subcommands = ["projects", "proj", "init"]
            if self.args.subcommand not in exclude_subcommands and not self.args.quiet:
                # Print the current project information to try to avoid
                # confusion
                selected_project = self.projects_conf["project"]
                proj = projmod.Project(
                    selected_project,
                    self.projects_conf["projects"][selected_project],
                    self.projects_conf.filename,
                )
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
                        "class": core_class,
                        "module": module,
                        "mfile": module.__file__,
                    }

    def _initialize(self):
        self._load_config()

        log_file = self.args.log or None
        if log_file and not self.args.quiet:
            print(f"Logging output sent to: {log_file}")
        log_utils.setup_logger(self.args, log_file=log_file)
        logging.info("Logging level includes INFO.")
        logging.debug("Logging level includes DEBUG.")
        logging.info(f"PROJECTS_PATH: {self.PROJECTS_PATH}")

    def _load_config(self):
        if not os.path.isfile(self.PROJECTS_FILE):
            # If projects.conf file doesn't exist then we need to run the
            # initial setup.
            print("No project config file detected.")
            print("Please select a project setup option:")
            print("(1) Initialize the current directory as a gmrecords")
            print("    project, which will contain data and conf")
            print("    subdirectories.")
            print("(2) Setup a project with data and conf locations that")
            print("    are independent of the current directory.")
            response = int(input("> "))
            if response not in [1, 2]:
                print("Not a valid response. Exiting.")
                sys.exit(0)
            elif response == 1:
                init.InitModule().main(self)
                sys.exit(0)
            else:
                self._initial_setup()

        self.projects_conf = configobj.ConfigObj(self.PROJECTS_FILE, encoding="utf-8")
        self._validate_projects_config()
        # self.current_project gets set by _validate_projects_config if it is
        # successful.
        if not hasattr(self, "current_project"):
            print("Project validation failed.")
            print("This likely has occurred due to errors in the project conf file: ")
            print(f"    {self.PROJECTS_FILE}")
            print("Deleting this file and creating a new one with:")
            print("    gmrecords proj -c")
            print("will likely solve the problem.")
            print("Exiting.")
            sys.exit()

        self.conf_path = os.path.abspath(
            os.path.join(
                self.PROJECTS_FILE, os.pardir, self.current_project["conf_path"]
            )
        )
        self.data_path = os.path.abspath(
            os.path.join(
                self.PROJECTS_FILE, os.pardir, self.current_project["data_path"]
            )
        )

        if os.getenv("CALLED_FROM_PYTEST") is not None:
            self.conf_path = const.CONFIG_PATH_TEST  # ~/gmptest
            test_conf_file = os.path.normpath(
                os.path.join(const.DATA_DIR, const.CONFIG_FILE_TEST)  # config_test.yml
            )
            if not os.path.exists(self.conf_path):
                os.mkdir(self.conf_path)
            shutil.copyfile(
                test_conf_file, os.path.join(self.conf_path, const.CONFIG_FILE_TEST)
            )

        if (not os.path.exists(self.conf_path)) or (not os.path.exists(self.data_path)):
            print(
                "Config and/or data directory does not exist for project: "
                + self.project
            )
            config = self.projects_conf
            project = self.project

            conf_path = config["projects"][project]["conf_path"]
            if os.path.exists(conf_path):
                question = f"Okay to delete everything in: {conf_path}?\n"
                if not prompt.query_yes_no(question, default="yes"):
                    shutil.rmtree(conf_path, ignore_errors=True)
                    print(f"\tDeleted conf directory {conf_path}:")

            data_path = config["projects"][project]["data_path"]
            if os.path.exists(data_path):
                question = f"Okay to delete everything in: {data_path}?\n"
                if not prompt.query_yes_no(question, default="yes"):
                    shutil.rmtree(data_path, ignore_errors=True)
                    print(f"\tDeleted conf directory {data_path}:")

            del config["projects"][project]

            if config["projects"].keys() == []:
                print("No remaining projects in projects.conf")
                default = None
                newproject = "None"
            else:
                default = config["projects"].keys()[0]
                newproject = projmod.Project(
                    default, config["projects"][default], config.filename
                )
            config["project"] = default

            config.filename = self.PROJECTS_FILE
            config.write()
            print(f"Deleted project: {project}")

            print("\nSet to new project:\n")
            print(newproject)
            sys.exit(0)

        # Only run get_config for assemble and projects
        subcommands_need_conf = ["download", "assemble", "auto_shakemap"]
        if self.args.func.command_name in subcommands_need_conf:
            self.conf = configmod.get_config(config_path=self.conf_path)

    def _validate_projects_config(self):
        if "CALLED_FROM_PYTEST" in os.environ:
            self.project = self.projects_conf["project"]
            self.current_project = self.projects_conf["projects"][self.project]
            return

        # Check that all of the listed projects have the required keys and valid paths
        bad_projs = []
        for proj_name, proj in self.projects_conf["projects"].items():
            if ("conf_path" not in proj) or ("data_path" not in proj):
                bad_projs.append(proj_name)
                continue
            conf_path = os.path.abspath(
                os.path.join(self.PROJECTS_FILE, os.pardir, proj["conf_path"])
            )
            data_path = os.path.abspath(
                os.path.join(self.PROJECTS_FILE, os.pardir, proj["data_path"])
            )
            if not (os.path.isdir(conf_path) and os.path.isdir(data_path)):
                bad_projs.append(proj_name)
        for bad in bad_projs:
            print(f'Problem encountered in "{bad}" project. Deleting.')
            self.projects_conf["projects"].pop(bad)

        # Check that the selected project is in the list of projects
        self.project = self.projects_conf["project"]
        if self.project in self.projects_conf["projects"]:
            self.current_project = self.projects_conf["projects"][self.project]
        else:
            if len(self.projects_conf["projects"]):
                new_proj = self.projects_conf["projects"].keys()[0]
                print(f'The currently configured project ("{self.project}") is not in ')
                print("the list of available projects. ")
                print(f'Switching to the "{new_proj}" project.')
                self.project = new_proj
                self.current_project = self.projects_conf["projects"][self.project]
                self.projects_conf["project"] = new_proj
                self.projects_conf.write()

    def _initial_setup(self):
        """
        Initial setup of ~/.gmprogress/projects.conf; essentially invoke
        # gmrecords projects -c
        """
        if not os.path.isdir(self.PROJECTS_PATH):
            os.mkdir(self.PROJECTS_PATH)
        empty_conf = configobj.ConfigObj(encoding="utf-8")
        empty_conf.filename = self.PROJECTS_FILE
        projmod.create(empty_conf)
        # Need to exit here because if gmp projects -c is called when there is
        # no prior setup, the user would otherwise be forced to setup two
        # projects.
        sys.exit(0)

    def _parse_command_line(self):
        """Parse command line arguments."""
        # Main program parser
        description = """
        gmrecords is a program for retrieving and processing ground motion
        records, as well as exporting commonly used station and waveform
        parameters for earthquake hazard analysis.
        """
        self.parser = argparse.ArgumentParser(description=description)
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument(
            "-d",
            "--debug",
            action="store_true",
            help="Print all informational messages.",
        )
        group.add_argument(
            "-q", "--quiet", action="store_true", help="Print only errors."
        )
        self.parser.add_argument(
            "-v",
            "--version",
            action="version",
            version="%(prog)s " + VERSION,
            help="Print program version.",
        )
        self.parser.add_argument(
            "-l",
            "--log",
            action="store",
            type=str,
            default=None,
            help="Path to log file; if provided, loging is directed to this file.",
        )

        # Parsers for subcommands
        subparsers = self.parser.add_subparsers(
            title="Subcommands", dest="subcommand", metavar="<command> (<aliases>)"
        )

        # Get subcommands and their arguments
        self.load_subcommands()
        parsers = []
        for cname, cdict in self.classes.items():
            command_description = inspect.getdoc(cdict["class"])
            parsers.append(
                subparsers.add_parser(
                    cname, help=command_description, aliases=cdict["class"].aliases
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
        return self.parser.parse_args()
