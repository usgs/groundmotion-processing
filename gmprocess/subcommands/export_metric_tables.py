import os
import sys
import logging


from gmprocess.subcommands.base import SubcommandModule
from gmprocess.io.fetch_utils import get_events
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils.tables import set_precisions
from gmprocess.utils.constants import DEFAULT_FLOAT_FORMAT, DEFAULT_NA_REP


class ExportMetricTablesModule(SubcommandModule):
    """Export metric tables.
    """
    command_name = 'export_metric_tables'
    aliases = ('mtables', )

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
        """Export metric tables.

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
                'Creating tables for event %s...' % event.id)
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
            if len(labels):
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

            pstreams = workspace.getStreams(
                event.id, labels=[label])

            event_table, imc_tables, readmes = workspace.getTables(
                label, streams=pstreams, stream_label=label)
            ev_fit_spec, fit_readme = workspace.getFitSpectraTable(
                event.id, label, pstreams)
            workspace.close()

            outdir = gmp.data_path

            # Set the precisions for the imc tables, event table, and
            # fit_spectra table before writing
            imc_tables_formatted = {}
            for imc, imc_table in imc_tables.items():
                imc_tables_formatted[imc] = set_precisions(imc_table)
            event_table_formatted = set_precisions(event_table)
            df_fit_spectra_formatted = set_precisions(ev_fit_spec)

            filenames = ['events'] + \
                [imc.lower() for imc in imc_tables_formatted.keys()] + \
                [imc.lower() + '_README' for imc in readmes.keys()] + \
                ['fit_spectra_parameters', 'fit_spectra_parameters_README']

            files = [event_table_formatted] + list(
                imc_tables_formatted.values()) + list(
                readmes.values()) + [df_fit_spectra_formatted, fit_readme]

            output_format = gmp.args.output_format
            if output_format != 'csv':
                output_format = 'xlsx'

            for filename, df in dict(zip(filenames, files)).items():
                filepath = os.path.join(
                    outdir, filename + '.%s' % output_format)
                if os.path.exists(filepath):
                    if 'README' in filename:
                        continue
                    else:
                        mode = 'a'
                        header = False
                else:
                    mode = 'w'
                    header = True
                    self.append_file('Tables', filepath)
                if output_format == 'csv':
                    df.to_csv(filepath, index=False,
                              float_format=DEFAULT_FLOAT_FORMAT,
                              na_rep=DEFAULT_NA_REP,
                              mode=mode, header=header)
                else:
                    df.to_excel(filepath, index=False,
                                float_format=DEFAULT_FLOAT_FORMAT,
                                na_rep=DEFAULT_NA_REP,
                                mode=mode, header=header)

        self._summarize_files_created()
