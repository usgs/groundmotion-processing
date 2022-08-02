#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
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
        arg_dicts.ARG_DICTS["eventid"],
        arg_dicts.ARG_DICTS["textfile"],
        arg_dicts.ARG_DICTS["label"],
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

        for event in self.events:
            self.eventid = event.id
            logging.info(f"Creating provenance tables for event {self.eventid}...")

            self.open_workspace(event.id)
            self._get_pstreams()

            if not (hasattr(self, "pstreams") and len(self.pstreams) > 0):
                logging.info(
                    "No processed waveforms available. No provenance tables created."
                )
                continue

            provdata = self.workspace.getProvenance(
                self.eventid, labels=self.gmrecords.args.label
            )

            basename = os.path.join(
                self.event_dir(event.id),
                f"{gmrecords.project}_{gmrecords.args.label}_provenance"
            )
            if gmrecords.args.output_format == "csv":
                fname = basename + '.csv'
                self.append_file("Provenance", fname)
                provdata.to_csv(fname, index=False)
            else:
                fname = basename + '.xslx'
                self.append_file("Provenance", fname)
                provdata.to_excel(fname, index=False)

        self._summarize_files_created()
