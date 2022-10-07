#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib
import logging

from gmprocess.subcommands.lazy_loader import LazyLoader

configobj = LazyLoader("configobj", globals(), "configobj")

base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
const = LazyLoader("const", globals(), "gmprocess.utils.constants")
projects = LazyLoader("projects", globals(), "gmprocess.subcommands.projects")


class InitModule(base.SubcommandModule):
    """
    Initialize the current directory as a gmprocess project directory.
    """

    command_name = "init"

    arguments = []

    def main(self, gmrecords):
        """
        Initialize the current directory as a gmprocess project directory.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        config = configobj.ConfigObj(encoding="utf-8")
        cwd = pathlib.Path.cwd()
        local_proj_path = cwd / const.PROJ_CONF_DIR
        local_proj_path.mkdir(exist_ok=True)
        conf_file = local_proj_path / "projects.conf"
        if conf_file.is_file():
            msg = (
                f"Current directory '{local_proj_path}' already contains project "
                "configurations. Exiting. "
                "Run 'gmrecords projects -l' to list the current projects."
            )
            raise IOError(msg)
        config.filename = conf_file

        projects.create(config, use_cwd=True)
