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


class ExportProvenanceTablesModule(base.SubcommandModule):
    """Export provenance tables.
    """
    command_name = 'export_provenance_tables'
    aliases = ('ptables', )

    arguments = [
        arg_dicts.ARG_DICTS['eventid'],
        arg_dicts.ARG_DICTS['textfile'],
        arg_dicts.ARG_DICTS['label'],
        arg_dicts.ARG_DICTS['output_format']
    ]

    def main(self, gmrecords):
        """Export provenance tables.

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
                'Creating provenance tables for event %s...' % self.eventid)
            event_dir = os.path.normpath(
                os.path.join(gmrecords.data_path, self.eventid))
            workname = os.path.join(event_dir, const.WORKSPACE_NAME)
            if not os.path.isfile(workname):
                logging.info(
                    'No workspace file found for event %s. Please run '
                    'subcommand \'assemble\' to generate workspace file.'
                    % self.eventid)
                logging.info('Continuing to next event.')
                continue

            self.workspace = ws.StreamWorkspace.open(workname)
            self._get_pstreams()

            if not (hasattr(self, 'pstreams') and len(self.pstreams) > 0):
                logging.info('No processed waveforms available. No provenance '
                             'tables created.')
                self.workspace.close()
                continue

            provdata = self.workspace.getProvenance(
                self.eventid, labels=self.gmrecords.args.label)
            self.workspace.close()

            basename = '%s_%s_provenance' % (
                gmrecords.project, gmrecords.args.label)
            if gmrecords.args.output_format == 'csv':
                csvfile = os.path.join(event_dir, '%s.csv' % basename)
                self.append_file('Provenance', csvfile)
                provdata.to_csv(csvfile, index=False)
            else:
                excelfile = os.path.join(event_dir, '%s.xlsx' % basename)
                self.append_file('Provenance', excelfile)
                provdata.to_excel(excelfile, index=False)

        self._summarize_files_created()
