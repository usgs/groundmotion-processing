#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
from configobj import ConfigObj

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.utils import constants
from gmprocess.subcommands.projects import create


class InitModule(SubcommandModule):
    """
    Initialize the current directory as a gmprocess project directory.
    """
    command_name = 'init'

    arguments = []

    def main(self, eqprocess):
        """
        Initialize the current directory as a gmprocess project directory.

        Args:
            eqprocess:
                EQprocessApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        config = ConfigObj(encoding='utf-8')
        cwd = os.getcwd()
        local_proj_path = os.path.join(cwd, constants.PROJ_CONF_DIR)
        if not os.path.isdir(local_proj_path):
            os.mkdir(local_proj_path)
        conf_file = os.path.join(local_proj_path, 'projects.conf')
        config.filename = conf_file

        create(config, cwd=True)

        sys.exit(0)
