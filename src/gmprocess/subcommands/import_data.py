#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shutil
from pathlib import Path
from distutils.dir_util import copy_tree
import logging

from gmprocess.io.utils import flatten_directory
from gmprocess.subcommands.lazy_loader import LazyLoader

base = LazyLoader("base", globals(), "gmprocess.subcommands.base")


class ImportModule(base.SubcommandModule):
    """Import data for an event into the project data directory."""

    command_name = "import"

    arguments = [
        {
            "short_flag": "-p",
            "long_flag": "--path",
            "help": ("Path to file or directory containing data to import."),
            "type": str,
            "default": None,
        },
    ]

    def main(self, gmrecords):
        """
        Import data for an event into the project data directory.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")
        self.gmrecords = gmrecords
        self._check_arguments()

        import_path = Path(self.gmrecords.args.path)

        self._get_events()

        if self.events is None:
            raise ValueError("Please provide a valid event id.")

        if len(self.events) > 1:
            raise ValueError("Can only import data for one event at a time.")

        logging.info(f"Number of events to download: {len(self.events)}")
        for ievent, event in enumerate(self.events):
            logging.info(
                f"Importing event {event.id} ({1+ievent} of {len(self.events)})..."
            )
            event_dir = gmrecords.data_path / event.id
            event_dir.mkdir(exist_ok=True)

            raw_dir = event_dir / "raw"
            raw_dir.mkdir(exist_ok=True)

            if import_path.is_file():
                import_file = import_path.name
                src = import_path
                dst = raw_dir / import_file
                logging.info(f"Importing {str(src)}")
                shutil.copy(src, dst)
            elif import_path.is_dir():
                src = import_path
                dst = raw_dir
                copy_tree(str(src), str(dst))
            else:
                raise ValueError("Please provide a valid path to a file or directory")
            flatten_directory(raw_dir)
            logging.info(f"Event {event.id} complete.")
