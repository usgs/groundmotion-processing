#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import platform
import re
import logging
import shutil

from gmprocess.subcommands.lazy_loader import LazyLoader

ryaml = LazyLoader("yaml", globals(), "ruamel.yaml")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
prompt = LazyLoader("prompt", globals(), "gmprocess.utils.prompt")


# Regular expression for checking valid email
re_email = r"^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$"


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
            "help": "Switch from current project to PROJECT.",
            "type": str,
            "metavar": "PROJECT",
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
            "help": "Delete existing project PROJECT.",
            "type": str,
            "metavar": "PROJECT",
            "default": None,
        },
    ]

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
        config = self.gmrecords.projects_conf
        configfile = self.gmrecords.PROJECTS_FILE

        if self.gmrecords.args.create:
            create(config)
            sys.exit(0)

        config = check_project_config(config)

        if args.list:
            projects = config["projects"]
            current = config["project"]
            for pname, pdict in projects.items():
                is_current = False
                if pname == current:
                    is_current = True
                project = Project(pname, pdict, config.filename, is_current=is_current)
                print("\n" + str(project) + "\n")
            sys.exit(0)

        if args.switch:
            newproject = args.switch
            if newproject not in config["projects"]:
                msg = "Project %s not in %s.  Run %s -l to see available projects."
                print(msg % (newproject, configfile, self.command_name))
                sys.exit(1)
            config["project"] = newproject
            config.filename = configfile
            config.write()
            sp = Project(
                newproject,
                config["projects"][newproject],
                config.filename,
                is_current=True,
            )
            print(f"\nSwitched to project: \n{str(sp)}\n")
            sys.exit(0)

        if args.delete:
            project = args.delete
            if project not in config["projects"]:
                msg = "Project %s not in %s.  Run '%s' -l to available projects."
                print(msg % (project, configfile, self.command_name))
                sys.exit(1)

            conf_path = os.path.normpath(
                os.path.join(
                    os.path.abspath(os.path.join(config.filename, os.pardir)),
                    config["projects"][project]["conf_path"],
                )
            )
            data_path = os.path.normpath(
                os.path.join(
                    os.path.abspath(os.path.join(config.filename, os.pardir)),
                    config["projects"][project]["data_path"],
                )
            )

            question = (
                "Are you sure you want to delete everything in:\n"
                f"{conf_path}\n--and--\n{data_path}?\n"
            )
            if not prompt.query_yes_no(question, default="yes"):
                sys.exit(0)

            shutil.rmtree(conf_path, ignore_errors=True)
            shutil.rmtree(data_path, ignore_errors=True)

            del config["projects"][project]

            if config["projects"].keys() == []:
                print("No remaining projects in projects.conf")
                default = None
                newproject = "None"
            else:
                default = config["projects"].keys()[0]
                newproject = Project(
                    default, config["projects"][default], config.filename
                )
            config["project"] = default

            config.filename = configfile
            config.write()
            print(f"Deleted project: {project}")
            print(f"\tDeleted conf directory {conf_path}:")
            print(f"\tDeleted data directory {data_path}:")

            print("\nSet to new project:\n")
            print(newproject)
            sys.exit(0)

        project = config["project"]
        projects = config["projects"]
        if project not in projects:
            msg = (
                "Current project %s not in %s. Edit your projects.conf "
                "file to match the specification."
            )
            print(msg % (project, configfile))
            sys.exit(1)
        sproj = Project(project, projects[project], projects.filename, is_current=True)
        print(sproj)
        sys.exit(0)


current_markers = {True: "**Current Project**", False: ""}


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
        self.current_marker = current_markers[is_current]

    def __repr__(self):
        fmt = "Project: %s %s\n\tConf Path: %s\n\tData Path: %s"
        base_dir = os.path.join(os.path.abspath(os.path.join(self.filename, os.pardir)))
        if platform.system() != "Windows":
            tpl = (
                self.name,
                self.current_marker,
                os.path.normpath(os.path.join(base_dir, self.conf_path)),
                os.path.normpath(os.path.join(base_dir, self.data_path)),
            )
        else:
            tpl = (self.name, self.current_marker, self.conf_path, self.data_path)
        return fmt % tpl


def check_project_config(config):
    """
    Validation checks on the project config. At least one project must exist
    (otherwise exit) and the paths for each project should exist, otherwise the
    project entry is removed.

    Args:
        config (ConfigObj):
            The ConfigObj instance.
    """
    # Check that at least one project exists
    if "projects" not in config:
        logging.error(
            'There are currently no projects. Use "gmrecords '
            'projects -c <project>" to create one.'
        )
        sys.exit(1)
    # Check that the paths for each project exist
    for project in config["projects"].keys():
        data_exists = os.path.isdir(
            os.path.join(
                os.path.abspath(os.path.join(config.filename, os.pardir)),
                config["projects"][project]["data_path"],
            )
        )
        delete_project = False
        if not data_exists:
            logging.warn(f"Data path for project {project} does not exist.")
            delete_project = True
        conf_exists = os.path.isdir(
            os.path.join(
                os.path.abspath(os.path.join(config.filename, os.pardir)),
                config["projects"][project]["conf_path"],
            )
        )
        if not conf_exists:
            logging.warn(f"Install path for project {project} does not exist.")
            delete_project = True
        if delete_project:
            logging.warn(f"Deleting project {project}.")
            del config["projects"][project]
            config["project"] = config["projects"].keys()[0]
            config.write()
    return config


def create(config, cwd=False):
    """Create a new gmrecords project.

    Args:
        config (ConfigObj):
            ConfigObj instance representing the parsed projects config.
        cwd (bool):
            Is this for initializing a "local" project in the current
            working directory?
    """
    project = input("Please enter a project title: [default] ")
    if not len(project.strip()):
        project = "default"
    if "projects" in config and project in config["projects"]:
        msg = (
            "Project '%s' already exists.  Run 'gmrecords projects "
            "-l' to see existing projects."
        )
        print(msg % project)
        sys.exit(1)

    if not cwd:
        proj_dir = constants.PROJECTS_PATH
        default_conf, default_data = prompt.get_default_project_paths(project)
        new_conf_path, new_data_path = prompt.set_project_paths(
            default_conf, default_data
        )
    else:
        cwd = os.getcwd()
        proj_dir = os.path.join(cwd, ".gmprocess")
        new_conf_path = os.path.join(cwd, "conf")
        new_data_path = os.path.join(cwd, "data")
        for p in [new_conf_path, new_data_path]:
            if not os.path.isdir(p):
                os.mkdir(p)

    print("Please enter your name and email. This information will be added")
    print("to the config file and reported in the provenance of the data")
    print("processed in this project.")
    user_info = {}
    user_info["name"] = input("\tName: ")
    if not len(user_info["name"].strip()):
        print("User name is required. Exiting.")
        sys.exit(0)
    user_info["email"] = input("\tEmail: ")
    if not re.search(re_email, user_info["email"]):
        print("Invalid Email. Exiting.")
        sys.exit(0)

    # Apparently, relpath doesn't work for Windows, at least with the Azure
    # CI builds
    if platform.system() != "Windows":
        new_conf_path = os.path.relpath(
            new_conf_path, os.path.join(config.filename, os.pardir)
        )
        new_data_path = os.path.relpath(
            new_data_path, os.path.join(config.filename, os.pardir)
        )

    if "projects" not in config:
        config["projects"] = {}

    config["projects"][project] = {
        "conf_path": new_conf_path,
        "data_path": new_data_path,
    }

    config["project"] = project
    config.write()
    sproj = Project(project, config["projects"][project], config.filename)
    print(f"\nCreated project: {sproj}")

    yaml = ryaml.YAML()
    yaml.indent(mapping=4)
    yaml.preserve_quotes = True
    user_conf = {}
    user_conf["user"] = user_info
    if os.getenv("CALLED_FROM_PYTEST") is None:
        proj_conf_file = os.path.join(proj_dir, new_conf_path, "user.yml")
    else:
        proj_dir = constants.CONFIG_PATH_TEST
        proj_conf_file = os.path.join(proj_dir, "user.yml")
    with open(proj_conf_file, "w", encoding="utf-8") as yf:
        yaml.dump(user_conf, yf)
