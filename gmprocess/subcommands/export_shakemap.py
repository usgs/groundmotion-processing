#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.fetch_utils import save_shakemap_amps
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils.constants import WORKSPACE_NAME


class ExportShakeMapModule(SubcommandModule):
    """Export files for ShakeMap input.
    """
    command_name = 'export_shakemap'
    aliases = ('shakemap', )

    arguments = [
        ARG_DICTS['eventid'],
        ARG_DICTS['label']
    ]

    def main(self, gmrecords):
        """Export files for ShakeMap input.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        self.gmrecords = gmrecords
        self._get_events()

        for event in self.events:
            self.eventid = event.id
            logging.info(
                'Creating shakemap files for event %s...' % self.eventid)

            event_dir = os.path.join(gmrecords.data_path, event.id)
            workname = os.path.join(event_dir, WORKSPACE_NAME)
            if not os.path.isfile(workname):
                logging.info(
                    'No workspace file found for event %s. Please run '
                    'subcommand \'assemble\' to generate workspace file.'
                    % event.id)
                logging.info('Continuing to next event.')
                continue

            self.workspace = StreamWorkspace.open(workname)
            self._get_pstreams()
            self.workspace.close()

            if not hasattr(self, 'pstreams'):
                logging.info('No processed waveforms available. No shakemap '
                             'files created.')
                return

            # TODO: re-write this so that it uses the already computer values
            # in self.workspace.dataset.auxiliary_data.WaveFormMetrics
            # rather than recomputing the metrics from self.pstreams.
            shakemap_file, jsonfile = save_shakemap_amps(
                self.pstreams, event, event_dir)
            self.append_file('shakemap', shakemap_file)
            self.append_file('shakemap', jsonfile)

        self._summarize_files_created()
