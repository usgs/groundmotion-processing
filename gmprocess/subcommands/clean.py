#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import shutil
from glob import glob

from gmprocess.subcommands.lazy_loader import LazyLoader

base = LazyLoader("base", globals(), "gmprocess.subcommands.base")


class CleanModule(base.SubcommandModule):
    """Clean (i.e., remove) project data."""

    command_name = "clean"

    arguments = [
        {
            "short_flag": "-a",
            "long_flag": "--all",
            "help": "Remove all project files except raw data.",
            "default": False,
            "action": "store_true",
        },
        {
            "long_flag": "--raw",
            "help": "Remove all raw directories.",
            "default": False,
            "action": "store_true",
        },
        {
            "long_flag": "--workspace",
            "help": "Remove all workspace files.",
            "default": False,
            "action": "store_true",
        },
        {
            "long_flag": "--report",
            "help": "Remove all PDF reports.",
            "default": False,
            "action": "store_true",
        },
        {
            "long_flag": "--export",
            "help": "Remove all exported tables (.csv and .xlsx).",
            "default": False,
            "action": "store_true",
        },
        {
            "long_flag": "--plot",
            "help": "Remove plots (*.png, plots/*).",
            "default": False,
            "action": "store_true",
        },
        {
            "long_flag": "--html",
            "help": "Remove html maps.",
            "default": False,
            "action": "store_true",
        },
    ]

    def main(self, gmrecords):
        """
        Clean (i.e., remove) project data.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")
        self.gmrecords = gmrecords
        self._check_arguments()

        # ---------------------------------------------------------------------
        # At the project level
        data_path = gmrecords.data_path

        # Exported tables
        if gmrecords.args.all or gmrecords.args.export:
            self.__remove(data_path, ["*.xlsx", "*.csv"])

        # Regression
        if gmrecords.args.all or gmrecords.args.plot:
            self.__remove(data_path, ["*.png"])

        # ---------------------------------------------------------------------
        # Inside the event directories
        events = glob(os.path.join(data_path, "*/"))
        logging.info(f"Number of events: {len(events)}")
        for event in events:
            event_dir = os.path.normpath(os.path.join(data_path, event))
            if os.path.exists(event_dir):
                # Exported tables
                if gmrecords.args.all or gmrecords.args.export:
                    patterns = [
                        "*.xlsx",
                        "*.csv",
                        "*_groundmotions_dat.json",
                        "*_metrics.json",
                    ]
                    self.__remove(event_dir, patterns)

                # Workspace
                if gmrecords.args.all or gmrecords.args.workspace:
                    self.__remove(event_dir, ["*.h5", "*.hdf"])

                # Report
                if gmrecords.args.all or gmrecords.args.report:
                    self.__remove(event_dir, ["*_report_*.pdf"])

                # Raw
                if gmrecords.args.raw:
                    rawdir = os.path.normpath(os.path.join(event_dir, "raw"))
                    if os.path.isdir(rawdir):
                        try:
                            logging.info(f"Removing: {rawdir}")
                            shutil.rmtree(rawdir)
                        except BaseException as e:
                            logging.info(f"Error while deleting: {e}")

                # Plots
                if gmrecords.args.all or gmrecords.args.plot:
                    self.__remove(event_dir, ["*.png"])
                    plotsdir = os.path.normpath(os.path.join(event_dir, "plots"))
                    if os.path.isdir(plotsdir):
                        try:
                            logging.info(f"Removing: {plotsdir}")
                            shutil.rmtree(plotsdir)
                        except BaseException as e:
                            logging.info(f"Error while deleting: {e}")

                # HTML
                if gmrecords.args.all or gmrecords.args.html:
                    self.__remove(event_dir, ["*.html"])

    @staticmethod
    def __remove(base_dir, patterns):
        for pattern in patterns:
            matches = glob(os.path.join(base_dir, pattern))
            for match in matches:
                match = os.path.normpath(match)
                try:
                    logging.info(f"Removing: {match}")
                    os.remove(match)
                except BaseException as e:
                    logging.info(f"Error while deleting: {e}")
