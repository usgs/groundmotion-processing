#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging


from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils.constants import WORKSPACE_NAME


class ExportFailureTablesModule(SubcommandModule):
    """Export failure tables.
    """
    command_name = 'export_failure_tables'
    aliases = ('ftables', )

    arguments = [
        ARG_DICTS['eventid'],
        ARG_DICTS['label'], {
            'short_flag': '-t',
            'long_flag': '--type',
            'help': (
                'Output failure information, either in short form ("short"),'
                'long form ("long"), or network form ("net"). short: Two '
                'column table, where the columns are "failure reason" and '
                '"number of records". net: Three column table where the '
                'columns are "network", "number passed", and "number failed". '
                'long: Two column table, where columns are "station ID" and '
                '"failure reason".'),
            'type': str,
            'default': 'short',
            'choices': ['short', 'long', 'net']
        },
        ARG_DICTS['output_format']
    ]

    def main(self, gmp):
        """Export failure tables.

        Args:
            gmp: GmpApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        self.gmp = gmp
        self._get_events()

        for event in self.events:
            self.eventid = event.id
            logging.info(
                'Creating failure tables for event %s...' % self.eventid)
            event_dir = os.path.join(self.gmp.data_path, self.eventid)
            workname = os.path.join(event_dir, WORKSPACE_NAME)
            if not os.path.isfile(workname):
                logging.info(
                    'No workspace file found for event %s. Please run '
                    'subcommand \'assemble\' to generate workspace file.'
                    % self.eventid)
                logging.info('Continuing to next event.')
                continue

            self.workspace = StreamWorkspace.open(workname)
            self._get_pstreams()
            self.workspace.close()

            if self.gmp.args.type == 'short':
                index = 'Failure reason'
                col = ['Number of records']
            elif self.gmp.args.type == 'long':
                index = 'Station ID'
                col = ['Failure reason']
            elif self.gmp.args.type == 'net':
                index = 'Network'
                col = ['Number of passed records', 'Number of failed records']

            status_info = self.pstreams.get_status(self.gmp.args.type)
            base_file_name = os.path.join(
                event_dir,
                '%s_%s_failure_reasons_%s' % (
                    gmp.project, gmp.args.label, self.gmp.args.type)
            )

            if self.gmp.args.output_format == 'csv':
                csvfile = base_file_name + '.csv'
                self.append_file('Failure table', csvfile)
                status_info.to_csv(csvfile, header=col, index_label=index)
            else:
                excelfile = base_file_name + '.xlsx'
                self.append_file('Failure table', excelfile)
                status_info.to_excel(excelfile, header=col, index_label=index)

        self._summarize_files_created()
