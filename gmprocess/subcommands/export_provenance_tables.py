import os
import sys
import logging


from gmprocess.subcommands.base import SubcommandModule
from gmprocess.io.fetch_utils import get_events
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils.constants import DEFAULT_FLOAT_FORMAT, DEFAULT_NA_REP


class ExportProvenanceTablesModule(SubcommandModule):
    """Export provenance tables.
    """
    command_name = 'export_provenance_tables'
    aliases = ('ptables', )

    arguments = [
        {
            'short_flag': '-e',
            'long_flag': '--eventid',
            'help': ('Comcat event ID. If None (default) all events in '
                     'project data directory will be used.'),
            'type': str,
            'default': None,
            'nargs': '+'
        }, {
            'short_flag': '-o',
            'long_flag': '--output-format',
            'help': 'Output file format.',
            'type': str,
            'default': 'csv',
            'choices': ['excel', 'csv']
        }
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

        label = None

        for event in events:
            logging.info(
                'Creating provenance tables for event %s...' % event.id)
            event_dir = os.path.join(gmp.data_path, event.id)
            workname = os.path.join(event_dir, 'workspace.hdf')
            if not os.path.isfile(workname):
                logging.info(
                    'No workspace file found for event %s. Please run '
                    'subcommand \'assemble\' to generate workspace file.'
                    % event.id)
                logging.info('Continuing to next event.')
                continue
            workspace = StreamWorkspace.open(workname)
            labels = workspace.getLabels()

            if len(labels) > 1 and 'unprocessed' in labels:
                labels.remove('unprocessed')
            else:
                logging.info('No processed waveform data in workspace. Please '
                             'run assemble.')
                sys.exit(1)

            # If there are more than 1 processed labels, prompt user to select
            # one.
            if len(labels) > 1 and label is not None:
                print('Which label do you want to use?')
                for lab in labels:
                    print('\t%s' % lab)
                tmplab = input()
                if tmplab not in labels:
                    raise ValueError('%s not a valid label. Exiting.' % tmplab)
                else:
                    label = tmplab
            else:
                label = labels[0]

            provdata = workspace.getProvenance(
                event.id, labels=label)
            workspace.close()

            if gmp.args.output_format == 'csv':
                csvfile = os.path.join(event_dir, 'provenance.csv')
                self.append_file('Provenance', csvfile)
                provdata.to_csv(csvfile)
            else:
                excelfile = os.path.join(event_dir, 'provenance.xlsx')
                self.append_file('Provenance', excelfile)
                provdata.to_excel(excelfile, index=False)

        self._summarize_files_created()
