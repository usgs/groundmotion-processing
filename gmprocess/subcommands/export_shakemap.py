#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.fetch_utils import create_json
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils.constants import WORKSPACE_NAME


class ExportShakeMapModule(SubcommandModule):
    """Export files for ShakeMap input.
    """
    command_name = 'export_shakemap'
    aliases = ('shakemap', )

    arguments = [
        ARG_DICTS['eventid'],
        ARG_DICTS['label'],
        {
            'short_flag': '-x',
            'long_flag': '--expand-imts',
            'help': ('Use expanded IMTs. Currently this only means all the '
                     'SA that have been computed, plus PGA and PGV (if '
                     'computed). Could eventually expand for other IMTs also.'
                     ),
            'default': False,
            'action': 'store_true'
        }
    ]

    def main(self, gmrecords):
        """Export files for ShakeMap input.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        self.gmrecords = gmrecords
        self._check_arguments()
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
            self._get_labels()

            if not hasattr(self, 'pstreams'):
                logging.info('No processed waveforms available. No shakemap '
                             'files created.')
                self.workspace.close()
                continue

            expanded_imts = self.gmrecords.args.expand_imts
            jsonfile, stationfile, _ = create_json(
                self.workspace, event, event_dir, self.gmrecords.args.label,
                config=self.gmrecords.conf, expanded_imts=expanded_imts)

            self.workspace.close()
            self.append_file('shakemap', jsonfile)
            self.append_file('shakemap', stationfile)

        self._summarize_files_created()
