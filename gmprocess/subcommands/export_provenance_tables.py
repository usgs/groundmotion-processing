import os
import sys
import logging


from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.fetch_utils import get_events
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils.constants import DEFAULT_FLOAT_FORMAT, DEFAULT_NA_REP


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

    def main(self, gmp):
        """Export provenance tables.

        Args:
            gmp: GmpApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        events = get_events(
            eventids=gmp.args.eventid,
            textfile=None,
            eventinfo=None,
            directory=gmp.data_path,
            outdir=None
        )

        self.label = gmp.args.label

        for event in events:
            self.eventid = event.id
            logging.info(
                'Creating provenance tables for event %s...' % self.eventid)
            event_dir = os.path.join(gmp.data_path, self.eventid)
            workname = os.path.join(event_dir, 'workspace.hdf')
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
                self.eventid, labels=self.label)
            self.workspace.close()

            if gmp.args.output_format == 'csv':
                csvfile = os.path.join(event_dir, 'provenance.csv')
                self.append_file('Provenance', csvfile)
                provdata.to_csv(csvfile, index=False)
            else:
                excelfile = os.path.join(event_dir, 'provenance.xlsx')
                self.append_file('Provenance', excelfile)
                provdata.to_excel(excelfile, index=False)

        self._summarize_files_created()
