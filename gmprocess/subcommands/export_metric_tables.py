import os
import logging


from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
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
        ARG_DICTS['eventid'],
        ARG_DICTS['label'],
        ARG_DICTS['output_format']
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

        self.label = gmp.args.label

        for event in events:
            self.eventid = event.id
            logging.info(
                'Creating tables for event %s...' % self.eventid)
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

            event_table, imc_tables, readmes = self.workspace.getTables(
                self.label, streams=self.pstreams, stream_label=None)
            ev_fit_spec, fit_readme = self.workspace.getFitSpectraTable(
                self.eventid, self.label, self.pstreams)
            self.workspace.close()

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
