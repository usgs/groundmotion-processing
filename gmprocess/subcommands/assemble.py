#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.fetch_utils import download
from gmprocess.utils.constants import WORKSPACE_NAME


class AssembleModule(SubcommandModule):
    """Assemble raw data and organize it into an ASDF file.
    """
    command_name = 'assemble'

    arguments = [
        ARG_DICTS['eventid'],
        ARG_DICTS['overwrite']
    ]

    def main(self, gmrecords):
        """
        Assemble data and organize it into an ASDF file.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)
        self.gmrecords = gmrecords

        self._get_events()
        print(self.events)

        logging.info('Number of events to assemble: %s' % len(self.events))
        for event in self.events:
            logging.info('Starting event: %s' % event.id)
            event_dir = os.path.join(gmrecords.data_path, event.id)
            if not os.path.exists(event_dir):
                os.makedirs(event_dir)
            workname = os.path.join(event_dir, WORKSPACE_NAME)
            workspace_exists = os.path.isfile(workname)
            if workspace_exists:
                logging.info("ASDF exists: %s" % workname)
                if not gmrecords.args.overwrite:
                    logging.info("The --overwrite argument not selected.")
                    logging.info("No action taken for %s." % event.id)
                    continue
                else:
                    logging.info(
                        "Removing existing ASDF file: %s" % workname
                    )
                    os.remove(workname)

            # Todo: probably want to break up `download` into finer steps to
            # call here. Also, there are files created besides workspace
            # that are not getting tracked (e.g., raw data plots, event.json)
            workspace, _, _, _ = download(
                event=event,
                event_dir=event_dir,
                config=gmrecords.conf,
                directory=gmrecords.data_path
            )
            workspace.close()
            self.append_file('Workspace', workname)
        self._summarize_files_created()
