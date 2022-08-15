#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
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
        cwd = os.getcwd()
        local_proj_path = os.path.join(cwd, const.PROJ_CONF_DIR)
        if not os.path.isdir(local_proj_path):
            os.mkdir(local_proj_path)
        conf_file = os.path.join(local_proj_path, "projects.conf")
        config.filename = conf_file

        projects.create(config, cwd=True)

        sys.exit(0)
