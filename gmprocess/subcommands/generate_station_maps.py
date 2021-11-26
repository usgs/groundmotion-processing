#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

from gmprocess.subcommands.lazy_loader import LazyLoader
arg_dicts = LazyLoader(
    'arg_dicts', globals(), 'gmprocess.subcommands.arg_dicts')
base = LazyLoader('base', globals(), 'gmprocess.subcommands.base')
ws = LazyLoader('ws', globals(), 'gmprocess.io.asdf.stream_workspace')
const = LazyLoader('const', globals(), 'gmprocess.utils.constants')
report_utils = LazyLoader(
    'report_utils', globals(), 'gmprocess.utils.report_utils')


class GenerateHTMLMapModule(base.SubcommandModule):
    """Generate station maps (PNG and HTML).
    """
    command_name = 'generate_station_maps'
    aliases = ('maps', )

    arguments = [
        arg_dicts.ARG_DICTS['eventid'],
        arg_dicts.ARG_DICTS['textfile'],
        arg_dicts.ARG_DICTS['label']
    ]

    def main(self, gmrecords):
        """Generate summary report.

        This function generates station map (html and png).

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        for event in self.events:
            event_dir = os.path.join(self.gmrecords.data_path, event.id)
            workname = os.path.join(event_dir, const.WORKSPACE_NAME)
            if not os.path.isfile(workname):
                logging.info(
                    'No workspace file found for event %s. Please run '
                    'subcommand \'assemble\' to generate workspace file.'
                    % event.id)
                logging.info('Continuing to next event.')
                return False

            self.workspace = ws.StreamWorkspace.open(workname)
            ds = self.workspace.dataset
            station_list = ds.waveforms.list()
            self._get_labels()

            if len(station_list) == 0:
                logging.info('No processed waveforms available. No report '
                             'generated.')
                return False

            logging.info(
                'Generating station maps for event %s...' % event.id)

            pstreams = []
            for station_id in station_list:
                streams = self.workspace.getStreams(
                    event.id,
                    stations=[station_id],
                    labels=[self.gmrecords.args.label],
                    config=self.gmrecords.conf
                )
                if not len(streams):
                    raise ValueError('No matching streams found.')

                for stream in streams:
                    pstreams.append(stream)

            mapfiles = report_utils.draw_stations_map(
                pstreams, event, event_dir)
            for file in mapfiles:
                self.append_file('Station map', file)

        self._summarize_files_created()
