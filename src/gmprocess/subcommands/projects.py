#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import platform
import logging
import shutil

from pathlib import Path
from gmprocess.subcommands.lazy_loader import LazyLoader

ryaml = LazyLoader("yaml", globals(), "ruamel.yaml")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
prompt = LazyLoader("prompt", globals(), "gmprocess.utils.prompt")
configobj = LazyLoader("configobj", globals(), "configobj")


CURRENT_MARKERS = {True: "**Current Project**", False: ""}


class ProjectsModule(base.SubcommandModule):
    """
    Manage gmrecords projects.
    """

    command_name = "projects"
    aliases = ("proj",)

    arguments = [
        {
            "short_flag": "-l",
            "long_flag": "--list",
            "help": "List all configured gmrecords projects.",
            "default": False,
            "action": "store_true",
        },
        {
            "short_flag": "-s",
            "long_flag": "--switch",
            "help": "Switch from current project to <name>.",
            "type": str,
            "metavar": "<name>",
            "default": None,
        },
        {
            "short_flag": "-c",
            "long_flag": "--create",
            "help": "Create a project and switch to it.",
            "action": "store_true",
            "default": False,
        },
        {
            "short_flag": "-d",
            "long_flag": "--delete",
            "help": "Delete existing project <name>.",
            "type": str,
            "metavar": "<name>",
            "default": None,
        },
        {
            "short_flag": "-r",
            "long_flag": "--rename",
            "help": "Rename project <old> to <new>.",
            "type": str,
            "nargs": 2,
            "metavar": ("<old>", "<new>"),
            "default": None,
        },
        {
            "long_flag": "--set-conf",
            "help": "Set the conf path to <path> for project <name>.",
            "type": str,
            "nargs": 2,
            "metavar": ("<name>", "<path>"),
            "default": None,
        },
        {
            "long_flag": "--set-data",
            "help": "Set the data path to <path> for project <name>.",
            "type": str,
            "nargs": 2,
            "metavar": ("<name>", "<path>"),
            "default": None,
        },
    ]

    epilog = """
    In order to simplify the command line interface, the gmrecords command makes use of
    "projects". You can have many projects configured on your system, and a project can
    have data from many events. A project is essentially a way to encapsulate the
    configuration and data directories so that they do not need to be specified as
    command line arguments.

    `gmrecords` first checks the current directory for the presence of
    `./.gmprocess/projects.conf` (this is called a "local" or "directory" project); if
    that is not found then it looks for the presence of `~/.gmprocess/projects.conf`
    (this is called a "system" level project).

    Within the `projects.conf` file, the key `project` indicates which the currently
    selected project. Multiple projects can be included in a `projects.conf` file.

    The project name is then stored as a key at the top level, which itself has keys
    `data_path` and `conf_path`. The `data_path` points to the directory where data
    is stored, and organized at the top level by directories named by event id. The
    `conf_path` points to the directory that holds configuration options in YML files.
    """

    def main(self, gmrecords):
        """
        Manage gmrecords projects.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()

        args = self.gmrecords.args
        self.config = self.gmrecords.projects_conf
        self.config_filepath = self.gmrecords.projects_file

        if self.gmrecords.args.create:
            self.create_project()
            return

        if not self.config:
            print(f"Could not find project configuration file {self.config_filepath}.")
            return
        if len(self.config["projects"]) == 0:
            print(f"No projects in {self.config_filepath}.")

        if args.list:
            self.list_projects()
        elif args.switch:
            self.switch_project(args.switch)
        elif args.delete:
            self.delete_project(args.delete)
        elif args.rename:
            source, target = args.rename
            self.rename_project(source, target)
        elif args.set_conf:
            proj_name, conf_path = args.set_conf
            self._set_path(proj_name, conf_path, "conf_path")
        elif args.set_data:
            proj_name, data_path = args.set_data
            self._set_path(proj_name, data_path, "data_path")
        else:
            raise NotImplementedError("Subcommand projects option not implemented.")

    def list_projects(self):
        projects = self.config["projects"]
        for name in projects.keys():
            project = Project.from_config(self.config, name)
            print("\n" + str(project) + "\n")

    def switch_project(self, target):
        if target not in self.config["projects"]:
            msg = (
                f"Project '{target}' not in {self.config_filepath}. "
                f"Run 'gmrecords {self.command_name} -l' to see available projects."
            )
            raise IOError(msg)
        self.config["project"] = target
        self.config.write()
        sp = Project.from_config(self.config, target)
        print(f"\nSwitched to project: \n{str(sp)}\n")

    def delete_project(self, target):
        if target not in self.config["projects"]:
            msg = (
                f"Project '{target}' not in {self.config_filepath}. "
                f"Run 'gmrecords {self.command_name} -l' to see available projects."
            )
            logging.error(msg)
            return

        config_filepath = self.config_filepath
        project_config = self.config["projects"][target]
        conf_path = (config_filepath.parent / project_config["conf_path"]).resolve()
        data_path = (config_filepath.parent / project_config["data_path"]).resolve()

        question = (
            "Are you sure you want to delete everything in:\n"
            f"\t{conf_path}\n\t--and--\n\t{data_path}?\n"
        )
        if not prompt.query_yes_no(question, default="yes"):
            return

        del self.config["projects"][target]
        shutil.rmtree(data_path, ignore_errors=True)
        shutil.rmtree(conf_path, ignore_errors=True)
        print(f"Deleted project: {target}")
        print(f"\tDeleted conf directory {conf_path}:")
        print(f"\tDeleted data directory {data_path}:")

        # If possible, set current project to first remaining project.
        if not len(self.config["projects"].keys()):
            print(f"No remaining projects in {self.config_filepath}.")
            current_name = None
            current_project = "None"
        else:
            current_name = self.config["projects"].keys()[0]
            current_project = Project.from_config(self.config, current_name)
        self.config["project"] = current_name
        self.config.write()
        print(f"\nCurrent {current_project}")

    def create_project(self):
        if not self.config:
            self.config = configobj.ConfigObj(encoding="utf-8")
            self.config.filename = self.config_filepath
        use_cwd = self.config_filepath.parent.parent == Path.cwd()
        create(self.config, use_cwd)

    def rename_project(self, source, target):
        self._check_project_name(source)
        self.config["projects"][target] = self.config["projects"].pop(source)
        if self.config["project"] == source:
            self.config["project"] = target
        self.config.write()
        print(f"Renamed '{source}' to '{target}'.")

    def _set_path(self, proj_name, path, key):
        self._check_project_name(proj_name)
        self.config["projects"][proj_name][key] = path
        self.config.write()
        print(f"Set {key} for '{proj_name}' to '{path}'.")

    def _check_project_name(self, name):
        if name not in self.config["projects"]:
            msg = (
                f"Project '{name}' not in {self.config_filepath}. "
                f"Run 'gmrecords {self.command_name} -l' to see available projects."
            )
            raise IOError(msg)


class Project(object):
    def __init__(self, name, indict, filename, is_current=False):
        """Project class.

        Args:
            name (str):
                Project name.
            indict (dict):
                Dictionary with keys 'conf_path' and 'data_path'.
            filename (str):
                Path to the projects conf file.
            is_current (bool):
                Is 'project' the currently selected project?
        """
        self.name = name
        self.filename = filename
        self.conf_path = indict["conf_path"]
        self.data_path = indict["data_path"]
        self.current_marker = CURRENT_MARKERS[is_current]

    def __repr__(self):
        fmt = "Project: %s %s\n\tConf Path: %s\n\tData Path: %s"
        cpath = (Path(self.filename).parent / self.conf_path).resolve()
        dpath = (Path(self.filename).parent / self.data_path).resolve()
        tpl = (self.name, self.current_marker, cpath, dpath)
        return fmt % tpl

    @staticmethod
    def from_config(config, name):
        """Create Project from projects configuration.

        Args:
            config (ConfigObj):
                Projects configuration.
            name (str):
                Name of project.
        """
        is_current = name == config["project"]
        return Project(name, config["projects"][name], config.filename, is_current)


def get_current(config):
    """Get current project from configuration.

    We assume the configuration has already been validated.

    Args:
        config (ConfigObj):
            Projects configuration.

    returns (str):
        Name of current project or None if there is no current project.
    """
    if config["project"] == "None":
        return
    else:
        return config["projects"][config["project"]]


def validate_projects_config(config, projects_filepath):
    """Validate projects configuration.

    raises IOError exception if projects configuration is invalid.

    Args:
        config (ConfigObj):
            Projects configuration.
        projects_filepath (pathlib.Path):
            Path to current projects configuration file.
    """

    def check_keys(config):
        """Check that all of the listed projects have the required keys and we
        have a current project.
        """
        if "projects" not in config:
            raise IOError("Projects configuration missing list of projects.")
        bad_projs = []
        for proj_name, proj in config["projects"].items():
            if ("conf_path" not in proj) or ("data_path" not in proj):
                bad_projs.append(proj_name)
                continue
        for bad in bad_projs:
            msg = (
                f"Project configuration '{bad}' missing 'conf_path' or 'data_path'."
                "Removing project configuration from memory."
            )
            logging.error(msg)
            config["projects"].pop(bad)

        # Check that the selected project is in the list of projects
        if "project" not in config:
            raise IOError(
                "Projects configuration missing 'project' to select current project."
            )
        current_name = config["project"]
        if current_name not in config["projects"]:
            msg = (
                f"Currently selected project {current_name} is not in the list of "
                "available projects."
            )
            raise IOError(msg)

    def check_project_paths(project, projects_filepath):
        """Check that project configuration paths are valid."""
        msg = ""
        conf_path = (projects_filepath.parent / project["conf_path"]).resolve()
        if not conf_path.is_dir():
            msg += f"Could not find 'conf_path' directory {conf_path}."

        data_path = (projects_filepath.parent / project["data_path"]).resolve()
        if not data_path.is_dir():
            msg += f"Could not find 'data_path' directory {data_path}."

        if len(msg):
            raise IOError(msg)

    try:
        check_keys(config)

        current_name = config["project"]
        check_project_paths(config["projects"][current_name], projects_filepath)
    except IOError:
        pass


def create(config, use_cwd=False):
    """Create a new gmrecords project.

    Args:
        config (ConfigObj):
            ConfigObj instance representing the parsed projects config.
        use_cwd (bool):
            Is this for initializing a "local" project in the current
            working directory?
    """
    project = input("Please enter a project title: [default] ")
    if not len(project.strip()):
        project = "default"
    if "projects" in config and project in config["projects"]:
        msg = (
            f"Project '{project}' already exists.  Run 'gmrecords projects "
            "-l' to see existing projects."
        )
        logging.error(msg)
        return

    if use_cwd:
        cwd = Path.cwd()
        default_conf_path = cwd / "conf"
        default_data_path = cwd / "data"
    else:
        project_path = Path("~").expanduser() / "gmprocess_projects" / project
        default_conf_path = project_path / "conf"
        default_data_path = project_path / "data"
    conf_path = prompt.get_directory("conf", default_conf_path).resolve()
    data_path = prompt.get_directory("data", default_data_path).resolve()
    conf_path.mkdir(parents=True, exist_ok=True)
    data_path.mkdir(parents=True, exist_ok=True)

    user_info = prompt.get_user_info()
    if not user_info:
        sys.exit(1)

    # Apparently, relpath doesn't work for Windows, at least with the Azure
    # CI builds
    if platform.system() != "Windows" and use_cwd:
        rel_path_loc = Path(config.filename).parents[1]
        conf_relpath = str(".." / conf_path.relative_to(rel_path_loc))
        data_relpath = str(".." / data_path.relative_to(rel_path_loc))
    else:
        conf_relpath = conf_path
        data_relpath = data_path

    if "projects" not in config:
        config["projects"] = {}
    config["projects"][project] = {
        "conf_path": conf_relpath,
        "data_path": data_relpath,
    }
    config["project"] = project

    Path(config.filename).parent.mkdir(exist_ok=True)
    config.write()
    proj = Project.from_config(config, project)
    print(f"\nCreated {proj}")

    yaml = ryaml.YAML()
    yaml.indent(mapping=4)
    yaml.preserve_quotes = True
    user_conf = {}
    user_conf["user"] = user_info
    if "CALLED_FROM_PYTEST" in os.environ:
        proj_conf_file = constants.CONFIG_PATH_TEST / "user.yml"
    else:
        proj_conf_file = conf_path / "user.yml"
    with open(proj_conf_file, "w", encoding="utf-8") as yf:
        yaml.dump(user_conf, yf)
