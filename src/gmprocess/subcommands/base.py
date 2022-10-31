#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from abc import ABC, abstractmethod
import logging
from pathlib import Path

from gmprocess.subcommands.lazy_loader import LazyLoader

base_utils = LazyLoader("base_utils", globals(), "gmprocess.utils.base_utils")
confmod = LazyLoader("confmod", globals(), "gmprocess.utils.config")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
const = LazyLoader("const", globals(), "gmprocess.utils.constants")


class SubcommandModule(ABC):
    """gmprocess base module."""

    @property
    @abstractmethod
    def command_name(self):
        """
        Name of subcommand: string, all lowercase.
        """
        raise NotImplementedError

    """Tuple class variable of subcommand aliases.
    """
    aliases = ()

    def __init__(self):
        """Dictionary instance variable to track files created by module."""
        self.files_created = {}

    def open_workspace(self, eventid):
        """Open workspace, add as attribute."""
        event_dir = Path(self.gmrecords.data_path) / eventid
        workname = event_dir / const.WORKSPACE_NAME
        if not workname.is_file():
            logging.info(
                f"No workspace file found for event {eventid}. Please run subcommand "
                "'assemble' to generate workspace file."
            )
            logging.info("Continuing to next event.")
            self.workspace = None
        else:
            self.workspace = ws.StreamWorkspace.open(workname)

    def close_workspace(self):
        """Close workspace."""
        self.workspace.close()

    @property
    @abstractmethod
    def arguments(self):
        """A list of dicts for each argument of the subcommands. Each dict
        should have the following keys: short_flag, long_flag, help, action,
        default.
        """
        raise NotImplementedError

    @abstractmethod
    def main(self, gmrecords):
        """
        All main methods should take one gmp object (a GMrecordsApp instance).
        """
        raise NotImplementedError

    @classmethod
    def list_arguments(cls):
        """List the arguments of the subcommand."""
        arg_list = []
        for arg in cls.arguments:
            arg_list.append(arg["long_flag"].replace("--", "").replace("-", "_"))
        return arg_list

    @classmethod
    def argugments_default_dict(cls):
        """List the arguments of the subcommand."""
        arg_list = cls.list_arguments()
        default_list = [arg["default"] for arg in cls.arguments]
        default_dict = dict(zip(arg_list, default_list))
        return default_dict

    def _check_arguments(self):
        """Check subcommand's arguments are present and fix if not.

        Puts in default value for arguments if argument is not specified.

        Motivation for this is for when the subcommand module is called
        directly, rather than from the gmrecords command line program.
        """
        args = self.gmrecords.args
        req_args = self.argugments_default_dict()
        for arg, val in req_args.items():
            if arg not in args:
                args.__dict__.update({arg: val})

    def append_file(self, tag, filename):
        """Convenience method to add file via tag to self.files_created."""
        if tag in self.files_created:
            self.files_created[tag].append(str(filename.resolve()))
        else:
            self.files_created[tag] = [str(filename.resolve())]

    def _summarize_files_created(self):
        if len(self.files_created):
            logging.info("The following files have been created:")
            for file_type, file_list in self.files_created.items():
                logging.info(f"File type: {file_type}")
                for fname in file_list:
                    logging.info(f"\t{fname}")
        else:
            logging.info("No new files created.")

    def _get_pstreams(self):
        """Convenience method for recycled code."""
        self._get_labels()
        if self.gmrecords.args.label is None:
            return

        config = self._get_config()

        self.pstreams = self.workspace.getStreams(
            self.eventid, labels=[self.gmrecords.args.label], config=config
        )

    def _get_events(self):
        # NOTE: as currently written, `get_events` will do the following,
        #  **stopping** at the first condition that is met:
        #     1) Use event ids if event id is not None
        #     2) Use textfile if it is not None
        #     3) Use event info if it is not None
        #     4) Use directory if it is not None
        #     5) Use outdir if it is not None
        # So in order to ever make use of the 'outdir' argument, we need to
        # set 'directory' to None, but otherwise set it to proj_data_path.
        #
        # This whole thing is really hacky and should probably be completely
        # rewritten.
        if hasattr(self.gmrecords.args, "data_source"):
            if self.gmrecords.args.data_source is None:
                # Use project directory from config
                temp_dir = self.gmrecords.data_path
                if not temp_dir.is_dir():
                    raise OSError(f"No such directory: {temp_dir}")
            elif self.gmrecords.args.data_source == "download":
                temp_dir = None
            else:
                temp_dir = self.gmrecords.args.data_source
                if not temp_dir.is_dir():
                    raise OSError(f"No such directory: {temp_dir}")
            self.download_dir = temp_dir
        else:
            self.download_dir = None

        info = (
            self.gmrecords.args.info if hasattr(self.gmrecords.args, "info") else None
        )
        tfile = (
            self.gmrecords.args.textfile
            if hasattr(self.gmrecords.args, "textfile")
            else None
        )
        if isinstance(self.gmrecords.args.eventid, str):
            # Need to strip in case there is whitespace
            self.gmrecords.args.eventid = [
                eid.strip() for eid in self.gmrecords.args.eventid.split(",")
            ]

        self.events = base_utils.get_events(
            eventids=self.gmrecords.args.eventid,
            textfile=tfile,
            eventinfo=info,
            directory=self.download_dir,
            outdir=self.gmrecords.data_path,
        )

    def _get_labels(self):
        labels = self.workspace.getLabels()
        if len(labels):
            labels.remove("unprocessed")
        if not len(labels):
            logging.info(
                f"No processed waveform data in: {self.workspace.dataset.filename}"
            )
            return

        # If there are more than 1 processed labels, prompt user to select
        # one.
        if (len(labels) > 1) and (self.gmrecords.args.label is None):
            print("\nWhich label do you want to use?")
            for lab in labels:
                print(f"\t{lab}")
            tmplab = input("> ")
            if tmplab not in labels:
                print(f"{tmplab} not a valid label. Exiting.")
                sys.exit(1)
            else:
                self.gmrecords.args.label = tmplab
        elif self.gmrecords.args.label is None:
            self.gmrecords.args.label = labels[0]

    def _get_config(self):
        if hasattr(self, "workspace") and hasattr(self.workspace, "config"):
            config = self.workspace.config
        else:
            config = confmod.get_config()
        return config
