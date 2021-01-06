#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging


from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils.constants import WORKSPACE_NAME


class ExportProvenanceTablesModule(SubcommandModule):
    """Export provenance tables.
    """
    command_name = 'export_provenance_tables'
    aliases = ('ptables', )

    arguments = [
        ARG_DICTS['eventid'],
        ARG_DICTS['label'],
        ARG_DICTS['output_format']
    ]

    def main(self, gmrecords):
        """Export provenance tables.

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
                'Creating provenance tables for event %s...' % self.eventid)
            event_dir = os.path.join(gmrecords.data_path, self.eventid)
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
