#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import copy

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
download_utils = LazyLoader(
    "download_utils", globals(), "gmprocess.utils.download_utils"
)


class DownloadModule(base.SubcommandModule):
    """Download data and organize it in the project data directory."""

    command_name = "download"

    arguments = [
        arg_dicts.ARG_DICTS["eventid"],
        arg_dicts.ARG_DICTS["textfile"],
        {
            "long_flag": "--info",
            "help": (
                "Single event information as ID TIME(YYYY-MM-DDTHH:MM:SS) "
                "LAT LON DEP MAG."
            ),
            "type": str,
            "default": None,
            "nargs": 7,
            "metavar": ("ID", "TIME", "LAT", "LON", "DEPTH", "MAG", "MAG_TYPE"),
        },
    ]

    def main(self, gmrecords):
        """
        Download data and organize it in the project data directory.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")
        self.gmrecords = gmrecords
        self._check_arguments()

        self._get_events()

        logging.info(f"Number of events to download: {len(self.events)}")
        for event in self.events:
            logging.info(f"Starting event: {event.id}")
            event_dir = os.path.normpath(os.path.join(gmrecords.data_path, event.id))
            if not os.path.exists(event_dir):
                os.makedirs(event_dir)

            download_utils.download(
                event=event, event_dir=event_dir, config=copy.deepcopy(gmrecords.conf)
            )
