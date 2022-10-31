#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
const = LazyLoader("const", globals(), "gmprocess.utils.constants")
sm_utils = LazyLoader("sm_utils", globals(), "gmprocess.utils.export_shakemap_utils")
confmod = LazyLoader("confmod", globals(), "gmprocess.utils.config")


class ExportShakeMapModule(base.SubcommandModule):
    """Export files for ShakeMap input."""

    command_name = "export_shakemap"
    aliases = ("shakemap",)

    arguments = [
        {
            "short_flag": "-x",
            "long_flag": "--expand-imts",
            "help": (
                "Use expanded IMTs. Currently this only means all the "
                "SA that have been computed, plus PGA and PGV (if "
                "computed). Could eventually expand for other IMTs also."
            ),
            "default": False,
            "action": "store_true",
        },
    ]

    def main(self, gmrecords):
        """Export files for ShakeMap input.

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
                f"Creating shakemap files for event {self.eventid} "
                f"({1+ievent} of {len(self.events)})..."
            )

            event_dir = gmrecords.data_path / event.id
            workname = event_dir / const.WORKSPACE_NAME
            if not workname.is_file():
                logging.info(
                    f"No workspace file found for event {event.id}. Please run "
                    "subcommand 'assemble' to generate workspace file."
                )
                logging.info("Continuing to next event.")
                continue

            self.workspace = ws.StreamWorkspace.open(workname)
            self._get_labels()
            config = self._get_config()

            expanded_imts = self.gmrecords.args.expand_imts
            jsonfile, stationfile, _ = sm_utils.create_json(
                self.workspace,
                event,
                event_dir,
                self.gmrecords.args.label,
                config=config,
                expanded_imts=expanded_imts,
            )

            self.workspace.close()
            if jsonfile is not None:
                self.append_file("shakemap", jsonfile)
            if stationfile is not None:
                self.append_file("shakemap", stationfile)

        self._summarize_files_created()
