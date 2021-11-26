#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging

from gmprocess.subcommands.lazy_loader import LazyLoader
distributed = LazyLoader('distributed', globals(), 'dask.distributed')

arg_dicts = LazyLoader(
    'arg_dicts', globals(), 'gmprocess.subcommands.arg_dicts')
base = LazyLoader('base', globals(), 'gmprocess.subcommands.base')
constants = LazyLoader('constants', globals(), 'gmprocess.utils.constants')
assemble_utils = LazyLoader(
    'assemble_utils', globals(), 'gmprocess.utils.assemble_utils')


class AssembleModule(base.SubcommandModule):
    """Assemble raw data and organize it into an ASDF file.
    """
    command_name = 'assemble'

    arguments = [
        arg_dicts.ARG_DICTS['eventid'],
        arg_dicts.ARG_DICTS['textfile'],
        arg_dicts.ARG_DICTS['overwrite'],
        arg_dicts.ARG_DICTS['num_processes']
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
                client = distributed.Client(
                    n_workers=gmrecords.args.num_processes)
            except BaseException as ex:
                print(ex)
                print("Could not create a dask client.")
                print("To turn off paralleization, use '--num-processes 0'.")
                sys.exit(1)
            futures = client.map(self._assemble_event, self.events)
            for result in distributed.as_completed(futures, with_results=True):
                print(result)
            client.shutdown()
        else:
            for event in self.events:
                self._assemble_event(event)

        self._summarize_files_created()

    def _assemble_event(self, event):
        logging.info('Starting event: %s' % event.id)
        event_dir = os.path.normpath(
            os.path.join(self.gmrecords.data_path, event.id))
        if not os.path.exists(event_dir):
            os.makedirs(event_dir)
        workname = os.path.normpath(
            os.path.join(event_dir, constants.WORKSPACE_NAME))
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

        workspace = assemble_utils.assemble(
            event=event,
            config=self.gmrecords.conf,
            directory=self.gmrecords.data_path,
            gmprocess_version=self.gmrecords.gmprocess_version
        )
        workspace.getGmprocessVersion()
        workspace.close()
        self.append_file('Workspace', workname)
        return event.id
