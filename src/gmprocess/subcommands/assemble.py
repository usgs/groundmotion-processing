#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from concurrent.futures import ProcessPoolExecutor

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
assemble_utils = LazyLoader(
    "assemble_utils", globals(), "gmprocess.utils.assemble_utils"
)


class AssembleModule(base.SubcommandModule):
    """Assemble raw data and organize it into an ASDF file."""

    command_name = "assemble"

    arguments = []

    def main(self, gmrecords):
        """
        Assemble data and organize it into an ASDF file.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")
        self.gmrecords = gmrecords
        self._check_arguments()

        self._get_events()

        logging.info(f"Number of events to assemble: {len(self.events)}")

        data_path = self.gmrecords.data_path
        overwrite = self.gmrecords.args.overwrite
        conf = self.gmrecords.conf
        version = self.gmrecords.gmprocess_version
        results = []

        if self.gmrecords.args.num_processes:
            futures = []
            executor = ProcessPoolExecutor(
                max_workers=self.gmrecords.args.num_processes
            )
            for ievent, event in enumerate(self.events):
                logging.info(
                    f"Assembling event {event.id} ({1+ievent} of {len(self.events)})..."
                )
                future = executor.submit(
                    self._assemble_event,
                    event,
                    data_path,
                    overwrite,
                    conf,
                    version,
                )
                futures.append(future)
            results = [future.result() for future in futures]
            executor.shutdown()
        else:
            for ievent, event in enumerate(self.events):
                logging.info(
                    f"Assembling event {event.id} ({1+ievent} of {len(self.events)})..."
                )
                results.append(
                    self._assemble_event(event, data_path, overwrite, conf, version)
                )

        for res in results:
            if res is not None:
                self.append_file("Workspace", res)

        self._summarize_files_created()

    # Note: I think that we need to make this a static method in order to be able to
    # call it with ProcessPoolExecutor.
    @staticmethod
    def _assemble_event(event, data_path, overwrite, conf, version):
        event_dir = data_path / event.id
        event_dir.mkdir(exist_ok=True)
        workname = event_dir / constants.WORKSPACE_NAME
        workspace_exists = workname.is_file()
        if workspace_exists:
            logging.info(f"ASDF exists: {str(workname)}")
            if not overwrite:
                logging.info("The --overwrite argument not selected.")
                logging.info(f"No action taken for {event.id}.")
                return None
            else:
                logging.info(f"Removing existing ASDF file: {str(workname)}")
                workname.unlink()

        workspace = assemble_utils.assemble(
            event=event,
            config=conf,
            directory=data_path,
            gmprocess_version=version,
        )
        workspace.close()
        return workname
