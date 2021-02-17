#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
from datetime import datetime

from dask.distributed import Client, as_completed

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils.constants import TAG_FMT
from gmprocess.utils.constants import WORKSPACE_NAME


class ProcessWaveformsModule(SubcommandModule):
    """Process waveform data.
    """
    command_name = 'process_waveforms'
    aliases = ('process', )

    # Note: do not use the ARG_DICT entry for label because the explanation is
    # different here: here it is used to set the label adn will default to
    # the date/time, but in subsequent subcommands it is used for selecting
    # from existing labels.
    arguments = [
        ARG_DICTS['eventid'], {
            'short_flag': '-l',
            'long_flag': '--label',
            'help': ('Processing label (single word, no spaces) to attach to '
                     'processed files. Defaults to the current time in '
                     'YYYYMMDDHHMMSS format.'),
            'type': str,
            'default': None,
        },
        ARG_DICTS['num_processes']
    ]

    def main(self, gmrecords):
        """Process data using steps defined in configuration file.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        self.gmrecords = gmrecords
        self._get_events()

        # get the process tag from the user or define by current datetime
        self.process_tag = (gmrecords.args.label or
                            datetime.utcnow().strftime(TAG_FMT))
        logging.info('Processing tag: %s' % self.process_tag)

        if gmrecords.args.num_processes:
            # parallelize processing on events
            try:
                client = Client(n_workers=gmrecords.args.num_processes)
            except BaseException as ex:
                print(ex)
                print("Could not create a dask client.")
                print("To turn off paralleization, use '--num-processes 0'.")
                sys.exit(1)
            futures = client.map(self._process_event, self.events)
            for result in as_completed(futures, with_results=True):
                print(result)
                # print('Completed event: %s' % result)
        else:
            for event in self.events:
                self._process_event(event)

        self._summarize_files_created()

    def _process_event(self, event):
        event_dir = os.path.join(self.gmrecords.data_path, event.id)
        workname = os.path.join(event_dir, WORKSPACE_NAME)
        if not os.path.isfile(workname):
            logging.info(
                'No workspace file found for event %s. Please run '
                'subcommand \'assemble\' to generate workspace file.')
            logging.info('Continuing to next event.')
            return event.id

        workspace = StreamWorkspace.open(workname)
        rstreams = workspace.getStreams(
            event.id, labels=['unprocessed'], config=self.gmrecords.conf)

        logging.info('Processing \'%s\' streams for event %s...'
                     % ('unprocessed', event.id))
        pstreams = process_streams(rstreams, event, config=self.gmrecords.conf)
        workspace.addStreams(event, pstreams, label=self.process_tag)
        workspace.close()
        return event.id
