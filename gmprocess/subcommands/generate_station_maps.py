#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils.constants import WORKSPACE_NAME
from gmprocess.utils.report_utils import draw_stations_map


class GenerateHTMLMapModule(SubcommandModule):
    """Generate station maps (PNG and HTML).
    """
    command_name = 'generate_station_maps'
    aliases = ('maps', )

    arguments = [
        ARG_DICTS['eventid'],
        ARG_DICTS['textfile'],
        ARG_DICTS['label']
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
            workname = os.path.join(event_dir, WORKSPACE_NAME)
            if not os.path.isfile(workname):
                logging.info(
                    'No workspace file found for event %s. Please run '
                    'subcommand \'assemble\' to generate workspace file.'
                    % event.id)
                logging.info('Continuing to next event.')
                return False

            self.workspace = StreamWorkspace.open(workname)
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
                stream = self.workspace.getStreams(
                    event.id,
                    stations=[station_id],
                    labels=[self.gmrecords.args.label],
                    config=self.gmrecords.conf
                )[0]
                pstreams.append(stream)

            mapfiles = draw_stations_map(pstreams, event, event_dir)
            for file in mapfiles:
                self.append_file('Station map', file)

        self._summarize_files_created()
