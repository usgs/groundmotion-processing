#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging


from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.fetch_utils import get_events
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils.tables import set_precisions
from gmprocess.utils.constants import DEFAULT_FLOAT_FORMAT, DEFAULT_NA_REP
from gmprocess.utils.constants import WORKSPACE_NAME


class ExportMetricTablesModule(SubcommandModule):
    """Export metric tables.
    """
    command_name = 'export_metric_tables'
    aliases = ('mtables', )

    arguments = [
        ARG_DICTS['eventid'],
        ARG_DICTS['label'],
        ARG_DICTS['output_format'],
        ARG_DICTS['overwrite']
    ]

    def main(self, eqprocess):
        """Export metric tables.

        Args:
            eqprocess:
                EQprocessApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        self.eqprocess = eqprocess
        self._get_events()

        for event in self.events:
            self.eventid = event.id
            logging.info(
                'Creating tables for event %s...' % self.eventid)
            event_dir = os.path.join(eqprocess.data_path, self.eventid)
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

            event_table, imc_tables, readmes = self.workspace.getTables(
                self.eqprocess.args.label, streams=self.pstreams)
            ev_fit_spec, fit_readme = self.workspace.getFitSpectraTable(
                self.eventid, self.eqprocess.args.label, self.pstreams)
            self.workspace.close()

            outdir = eqprocess.data_path

            # Set the precisions for the imc tables, event table, and
            # fit_spectra table before writing
            imc_tables_formatted = {}
            for imc, imc_table in imc_tables.items():
                imc_tables_formatted[imc] = set_precisions(imc_table)
            event_table_formatted = set_precisions(event_table)
            df_fit_spectra_formatted = set_precisions(ev_fit_spec)

            imc_list = [
                '%s_%s_metrics_%s' %
                (eqprocess.project, eqprocess.args.label, imc.lower())
                for imc in imc_tables_formatted.keys()
            ]
            readme_list = [
                '%s_%s_metrics_%s_README' %
                (eqprocess.project, eqprocess.args.label, imc.lower())
                for imc in readmes.keys()
            ]
            proj_lab = (eqprocess.project, eqprocess.args.label)

            event_filename = ['%s_%s_events' % proj_lab]
            filenames = event_filename + imc_list + readme_list + [
                '%s_%s_fit_spectra_parameters' % proj_lab,
                '%s_%s_fit_spectra_parameters_README' % proj_lab
            ]

            files = [event_table_formatted] + list(
                imc_tables_formatted.values()) + list(
                readmes.values()) + [df_fit_spectra_formatted, fit_readme]

            output_format = eqprocess.args.output_format
            if output_format != 'csv':
                output_format = 'xlsx'

            for filename, df in dict(zip(filenames, files)).items():
                filepath = os.path.join(
                    outdir, filename + '.%s' % output_format)
                if os.path.exists(filepath):
                    if 'README' in filename:
                        continue
                    else:
                        if self.eqprocess.args.overwrite:
                            logging.warning('File exists: %s' % filename)
                            logging.warning('Overwriting file: %s' % filename)
                            mode = 'w'
                            header = True
                        else:
                            logging.warning('File exists: %s' % filename)
                            logging.warning('Appending to file: %s' % filename)
                            mode = 'a'
                            header = False
                else:
                    mode = 'w'
                    header = True
                if output_format == 'csv':
                    df.to_csv(filepath, index=False,
                              float_format=DEFAULT_FLOAT_FORMAT,
                              na_rep=DEFAULT_NA_REP,
                              mode=mode, header=header)
                    if mode == "w":
                        self.append_file('Metric tables', filepath)
                else:
                    df.to_excel(filepath, index=False,
                                float_format=DEFAULT_FLOAT_FORMAT,
                                na_rep=DEFAULT_NA_REP,
                                mode=mode, header=header)
                    if mode == "w":
                        self.append_file('Metric tables', filepath)

        self._summarize_files_created()
