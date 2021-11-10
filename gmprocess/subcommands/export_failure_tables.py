#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

import pandas as pd

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
        ARG_DICTS['textfile'],
        ARG_DICTS['label'], {
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

    def main(self, gmrecords):
        """Export failure tables.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        failures = {}
        for event in self.events:
            self.eventid = event.id
            logging.info(
                'Creating failure tables for event %s...' % self.eventid)
            event_dir = os.path.join(self.gmrecords.data_path, self.eventid)
            workname = os.path.normpath(
                os.path.join(event_dir, WORKSPACE_NAME))
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

            if not (hasattr(self, 'pstreams') and len(self.pstreams) > 0):
                logging.info('No processed waveforms available. No failure '
                             'tables created.')
                continue

            status_info = self.pstreams.get_status(self.gmrecords.args.type)
            failures[event.id] = status_info

            base_file_name = os.path.normpath(os.path.join(
                event_dir,
                '%s_%s_failure_reasons_%s' % (
                    gmrecords.project, gmrecords.args.label,
                    self.gmrecords.args.type)
            ))

            if self.gmrecords.args.output_format == 'csv':
                csvfile = base_file_name + '.csv'
                self.append_file('Failure table', csvfile)
                status_info.to_csv(csvfile)
            else:
                excelfile = base_file_name + '.xlsx'
                self.append_file('Failure table', excelfile)
                status_info.to_excel(excelfile)

        if failures:
            comp_failures_path = os.path.normpath(os.path.join(
                self.gmrecords.data_path, '%s_%s_complete_failures.csv' % (
                    gmrecords.project, gmrecords.args.label)))
            if self.gmrecords.args.type == 'long':
                for idx, item in enumerate(failures.items()):
                    eqid, status = item
                    status = pd.DataFrame(status)
                    status['EarthquakeId'] = eqid
                    if idx == 0:
                        status.to_csv(comp_failures_path, mode='w')
                    else:
                        status.to_csv(comp_failures_path, mode='a',
                                      header=False)
            else:
                df_failures = pd.concat(failures.values())
                df_failures = df_failures.groupby(df_failures.index).sum()
                df_failures.to_csv(comp_failures_path)
            self.append_file('Complete failures', comp_failures_path)

        self._summarize_files_created()
