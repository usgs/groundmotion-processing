import os
import sys
import logging


from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.fetch_utils import get_events
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils.constants import DEFAULT_FLOAT_FORMAT, DEFAULT_NA_REP


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
                'Creating failure tables for event %s...' % self.eventid)
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
            self.workspace.close()

            if gmp.args.type == 'short':
                index = 'Failure reason'
                col = ['Number of records']
            elif gmp.args.type == 'long':
                index = 'Station ID'
                col = ['Failure reason']
            elif gmp.args.type == 'net':
                index = 'Network'
                col = ['Number of passed records', 'Number of failed records']

            status_info = self.pstreams.get_status(gmp.args.type)
            base_file_name = os.path.join(
                event_dir, 'failure_reasons_%s.csv' % gmp.args.type)

            if gmp.args.output_format == 'csv':
                csvfile = base_file_name + '.csv'
                self.append_file('Provenance', csvfile)
                status_info.to_csv(csvfile, header=col, index_label=index)
            else:
                excelfile = base_file_name + '.xlsx'
                self.append_file('Provenance', excelfile)
                status_info.to_excel(excelfile, header=col, index_label=index)

        self._summarize_files_created()
