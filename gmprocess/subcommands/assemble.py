#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging

from dask.distributed import Client, as_completed

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.utils.assemble_utils import assemble
from gmprocess.utils.constants import WORKSPACE_NAME


class AssembleModule(SubcommandModule):
    """Assemble raw data and organize it into an ASDF file.
    """
    command_name = 'assemble'

    arguments = [
        ARG_DICTS['eventid'],
        ARG_DICTS['textfile'],
        ARG_DICTS['overwrite'],
        ARG_DICTS['num_processes']
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
        self._check_arguments()

        self._get_events()

        logging.info('Number of events to assemble: %s' % len(self.events))

        if gmrecords.args.num_processes:
            # parallelize processing on events
            try:
                client = Client(n_workers=gmrecords.args.num_processes)
            except BaseException as ex:
                print(ex)
                print("Could not create a dask client.")
                print("To turn off paralleization, use '--num-processes 0'.")
                sys.exit(1)
            futures = client.map(self._assemble_event, self.events)
            for result in as_completed(futures, with_results=True):
                print(result)
            client.shutdown()
        else:
            for event in self.events:
                self._assemble_event(event)

        self._summarize_files_created()

    def _assemble_event(self, event):
        logging.info('Starting event: %s' % event.id)
        event_dir = os.path.join(self.gmrecords.data_path, event.id)
        if not os.path.exists(event_dir):
            os.makedirs(event_dir)
        workname = os.path.join(event_dir, WORKSPACE_NAME)
        workspace_exists = os.path.isfile(workname)
        if workspace_exists:
            logging.info("ASDF exists: %s" % workname)
            if not self.gmrecords.args.overwrite:
                logging.info("The --overwrite argument not selected.")
                logging.info("No action taken for %s." % event.id)
                return event.id
            else:
                logging.info(
                    "Removing existing ASDF file: %s" % workname
                )
                os.remove(workname)

        workspace = assemble(
            event=event,
            config=self.gmrecords.conf,
            directory=self.gmrecords.data_path
        )
        workspace.close()
        self.append_file('Workspace', workname)
        return event.id
