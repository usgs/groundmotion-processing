#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
const = LazyLoader("const", globals(), "gmprocess.utils.constants")


class ExportProvenanceTablesModule(base.SubcommandModule):
    """Export provenance tables."""

    command_name = "export_provenance_tables"
    aliases = ("ptables",)

    arguments = [
        arg_dicts.ARG_DICTS["output_format"],
    ]

    def main(self, gmrecords):
        """Export provenance tables.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        for ievent, event in enumerate(self.events):
            self.eventid = event.id
            logging.info(
                f"Creating provenance tables for event {self.eventid} "
                f"({1+ievent} of {len(self.events)})..."
            )
            event_dir = gmrecords.data_path / self.eventid

            workname = event_dir / const.WORKSPACE_NAME
            if not workname.is_file():
                logging.info(
                    f"No workspace file found for event {self.eventid}. Please run "
                    "subcommand 'assemble' to generate workspace file."
                )
                logging.info("Continuing to next event.")
                continue

            self.workspace = ws.StreamWorkspace.open(workname)
            self._get_pstreams()

            if not (hasattr(self, "pstreams") and len(self.pstreams) > 0):
                logging.info(
                    "No processed waveforms available. No provenance tables created."
                )
                self.workspace.close()
                continue

            provdata = self.workspace.getProvenance(
                self.eventid, labels=self.gmrecords.args.label
            )
            self.workspace.close()

            basename = f"{gmrecords.project_name}_{gmrecords.args.label}_provenance"
            if gmrecords.args.output_format == "csv":
                csvfile = event_dir / f"{basename}.csv"
                self.append_file("Provenance", csvfile)
                provdata.to_csv(csvfile, index=False)
            else:
                excelfile = event_dir / f"{basename}.xlsx"
                self.append_file("Provenance", excelfile)
                provdata.to_excel(excelfile, index=False)

        self._summarize_files_created()
