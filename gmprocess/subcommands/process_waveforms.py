#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

from gmprocess.subcommands.lazy_loader import LazyLoader
distributed = LazyLoader('distributed', globals(), 'dask.distributed')

arg_dicts = LazyLoader(
    'arg_dicts', globals(), 'gmprocess.subcommands.arg_dicts')
base = LazyLoader('base', globals(), 'gmprocess.subcommands.base')
const = LazyLoader('const', globals(), 'gmprocess.utils.constants')
ws = LazyLoader('ws', globals(), 'gmprocess.io.asdf.stream_workspace')
processing = LazyLoader(
    'processing', globals(), 'gmprocess.waveform_processing.processing')


class ProcessWaveformsModule(base.SubcommandModule):
    """Process waveform data.
    """
    command_name = 'process_waveforms'
    aliases = ('process', )

    # Note: do not use the ARG_DICT entry for label because the explanation is
    # different here: here it is used to set the label adn will default to
    # the date/time, but in subsequent subcommands it is used for selecting
    # from existing labels.
    arguments = [
        arg_dicts.ARG_DICTS['eventid'],
        arg_dicts.ARG_DICTS['textfile'], {
            'short_flag': '-l',
            'long_flag': '--label',
            'help': ('Processing label (single word, no spaces) to attach to '
                     'processed files. Default label is \'default\'.'),
            'type': str,
            'default': None,
        },
        arg_dicts.ARG_DICTS['num_processes']
    ]

    def main(self, gmrecords):
        """Process data using steps defined in configuration file.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        # get the process tag from the user or use "default" for tag
        self.process_tag = (gmrecords.args.label or
                            "default")
        logging.info('Processing tag: %s' % self.process_tag)

        for event in self.events:
            self._process_event(event)

        self._summarize_files_created()

    def _process_event(self, event):
        event_dir = os.path.join(self.gmrecords.data_path, event.id)
        workname = os.path.join(event_dir, const.WORKSPACE_NAME)
        if not os.path.isfile(workname):
            logging.info(
                'No workspace file found for event %s. Please run '
                'subcommand \'assemble\' to generate workspace file.')
            logging.info('Continuing to next event.')
            return event.id

        workspace = ws.StreamWorkspace.open(workname)
        ds = workspace.dataset
        station_list = ds.waveforms.list()

        processed_streams = []
        if self.gmrecords.args.num_processes > 0:
            futures = []
            client = distributed.Client(
                n_workers=self.gmrecords.args.num_processes)

        for station_id in station_list:
            # Cannot parallelize IO to ASDF file
            raw_streams = workspace.getStreams(
                event.id,
                stations=[station_id],
                labels=['unprocessed'],
                config=self.gmrecords.conf
            )

            if len(raw_streams):
                logging.info('Processing \'%s\' streams for event %s...'
                             % ('unprocessed', event.id))
                if self.gmrecords.args.num_processes > 0:
                    future = client.submit(
                        processing.process_streams, raw_streams, event,
                        self.gmrecords.conf)
                    futures.append(future)
                else:
                    processed_streams.append(
                        processing.process_streams(
                            raw_streams, event, self.gmrecords.conf)
                    )

        if self.gmrecords.args.num_processes > 0:
            # Collect the processed streams
            processed_streams = [future.result() for future in futures]
            client.shutdown()

        # Cannot parallelize IO to ASDF file
        for processed_stream in processed_streams:
            workspace.addStreams(
                event, processed_stream, label=self.process_tag,
                gmprocess_version=self.gmrecords.gmprocess_version)

        workspace.close()
        return event.id
