#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from distutils.dir_util import copy_tree
import logging
import zipfile
import tarfile

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")


class ImportModule(base.SubcommandModule):
    """Import data for an event into the project data directory."""

    command_name = "import"

    arguments = [
        arg_dicts.ARG_DICTS["eventid"],
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

        import_path = self.gmrecords.args.path

        self._get_events()

        if self.events is None:
            raise ValueError("Please provide a valid event id.")

        if len(self.events) > 1:
            raise ValueError("Can only import data for one event at a time.")

        logging.info(f"Number of events to download: {len(self.events)}")
        for event in self.events:
            logging.info(f"Starting event: {event.id}")
            event_dir = os.path.join(gmrecords.data_path, event.id)
            if not os.path.exists(event_dir):
                os.makedirs(event_dir)

            raw_dir = os.path.join(event_dir, "raw")
            if not os.path.exists(raw_dir):
                os.makedirs(raw_dir)

            if os.path.isfile(import_path):
                _, import_file = os.path.split(import_path)
                src = import_path
                dst = os.path.join(raw_dir, import_file)
                logging.info(f"Importing {src}")
                shutil.copy(src, dst)
                # Is this a zip or tar file? If so, extract
                if zipfile.is_zipfile(dst):
                    logging.info(f"Extracting {dst}")
                    with zipfile.ZipFile(dst, "r") as zfile:
                        zfile.extractall(raw_dir)
                    os.remove(dst)
                elif tarfile.is_tarfile(dst):
                    logging.info(f"Extracting {dst}")
                    with tarfile.open(dst, "r") as tar_file:
                        tar_file.extractall(raw_dir)
                    os.remove(dst)
            elif os.path.isdir(import_path):
                src = import_path
                dst = raw_dir
                copy_tree(src, dst)
            else:
                raise ValueError("Please provide a valid path to a file or directory")
            logging.info(f"Event {event.id} complete.")
