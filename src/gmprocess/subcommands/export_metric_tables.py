#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
const = LazyLoader("const", globals(), "gmprocess.utils.constants")
tables = LazyLoader("tables", globals(), "gmprocess.utils.tables")
confmod = LazyLoader("confmod", globals(), "gmprocess.utils.config")


class ExportMetricTablesModule(base.SubcommandModule):
    """Export metric tables."""

    command_name = "export_metric_tables"
    aliases = ("mtables",)

    arguments = [
        arg_dicts.ARG_DICTS["output_format"],
    ]

    def main(self, gmrecords):
        """Export metric tables.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        for ievent, event in enumerate(self.events):
            logging.info(
                f"Creating tables for event {event.id} "
                f"({1+ievent} of {len(self.events)})..."
            )
            self.eventid = event.id
            event_dir = gmrecords.data_path / self.eventid
            workname = event_dir / const.WORKSPACE_NAME
            if not workname.is_file():
                logging.warning(
                    f"No workspace file found for event {self.eventid}. Please run "
                    "subcommand 'assemble' to generate workspace file. "
                    "Continuing to next event."
                )
                continue

            self.workspace = ws.StreamWorkspace.open(workname)
            self._get_labels()
            config = self._get_config()

            if "StationMetrics" not in self.workspace.dataset.auxiliary_data:
                logging.warning(
                    f"Station metrics not found in workspace for event {self.eventid}."
                    "Continuing to next event."
                )
                continue

            event_table, imc_tables, readmes = self.workspace.getTables(
                self.gmrecords.args.label, config
            )
            ev_fit_spec, fit_readme = self.workspace.getFitSpectraTable(
                self.eventid, self.gmrecords.args.label, config
            )

            # We need to have a consistent set of frequencies for reporting the
            # SNR. For now, I'm going to take it from the SA period list, but
            # this could be changed to something else, or even be set via the
            # config file.
            snr_table, snr_readme = self.workspace.getSNRTable(
                self.eventid, self.gmrecords.args.label, config
            )
            self.workspace.close()

            outdir = gmrecords.data_path

            # Set the precisions for the imc tables, event table, and
            # fit_spectra table before writing
            imc_tables_formatted = {}
            for imc, imc_table in imc_tables.items():
                imc_tables_formatted[imc] = tables.set_precisions(imc_table)
            event_table_formatted = tables.set_precisions(event_table)
            if ev_fit_spec is not None:
                df_fit_spectra_formatted = tables.set_precisions(ev_fit_spec)
            else:
                df_fit_spectra_formatted = None

            imc_list = [
                f"{gmrecords.project_name}_{gmrecords.args.label}_metrics_{imc.lower()}"
                for imc in imc_tables_formatted.keys()
            ]
            readme_list = [
                "%s_%s_metrics_%s_README"
                % (gmrecords.project_name, gmrecords.args.label, imc.lower())
                for imc in readmes.keys()
            ]
            proj_lab = (gmrecords.project_name, gmrecords.args.label)

            filenames = (
                ["%s_%s_events" % proj_lab]
                + imc_list
                + readme_list
                + [
                    "%s_%s_fit_spectra_parameters" % proj_lab,
                    "%s_%s_fit_spectra_parameters_README" % proj_lab,
                ]
                + ["%s_%s_snr" % proj_lab, "%s_%s_snr_README" % proj_lab]
            )

            files = (
                [event_table_formatted]
                + list(imc_tables_formatted.values())
                + list(readmes.values())
                + [df_fit_spectra_formatted, fit_readme]
                + [snr_table, snr_readme]
            )

            output_format = gmrecords.args.output_format
            if output_format != "csv":
                output_format = "xlsx"

            for filename, df in dict(zip(filenames, files)).items():
                if df is None or df.size == 0:
                    continue
                filepath = outdir / (filename + f".{output_format}")
                if filepath.exists():
                    if "README" in filename:
                        continue
                    else:
                        if self.gmrecords.args.overwrite:
                            logging.info(f"Overwriting file: {filename}")
                            mode = "w"
                            header = True
                        else:
                            logging.info(f"Appending to file: {filename}")
                            mode = "a"
                            header = False
                else:
                    mode = "w"
                    header = True
                if output_format == "csv":
                    df.to_csv(
                        filepath,
                        index=False,
                        float_format=const.DEFAULT_FLOAT_FORMAT,
                        na_rep=const.DEFAULT_NA_REP,
                        mode=mode,
                        header=header,
                    )
                    if mode == "w":
                        self.append_file("Metric tables", filepath)
                else:
                    df.to_excel(
                        filepath,
                        index=False,
                        float_format=const.DEFAULT_FLOAT_FORMAT,
                        na_rep=const.DEFAULT_NA_REP,
                        mode=mode,
                        header=header,
                    )
                    if mode == "w":
                        self.append_file("Metric tables", filepath)

        self._summarize_files_created()
