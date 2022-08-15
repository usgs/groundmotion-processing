#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from concurrent.futures import ThreadPoolExecutor

from gmprocess.subcommands.lazy_loader import LazyLoader


arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
const = LazyLoader("const", globals(), "gmprocess.utils.constants")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
processing = LazyLoader(
    "processing", globals(), "gmprocess.waveform_processing.processing"
)
confmod = LazyLoader("confmod", globals(), "gmprocess.utils.config")


class ProcessWaveformsModule(base.SubcommandModule):
    """Process waveform data."""

    command_name = "process_waveforms"
    aliases = ("process",)

    # Note: do not use the ARG_DICT entry for label because the explanation is
    # different here.
    arguments = [
        arg_dicts.ARG_DICTS["eventid"],
        arg_dicts.ARG_DICTS["textfile"],
        {
            "short_flag": "-l",
            "long_flag": "--label",
            "help": (
                "Processing label (single word, no spaces) to attach to "
                "processed files. Default label is 'default'."
            ),
            "type": str,
            "default": None,
        },
        {
            "short_flag": "-r",
            "long_flag": "--reprocess",
            "help": ("Reprocess data using manually review information."),
            "default": False,
            "action": "store_true",
        },
        arg_dicts.ARG_DICTS["num_processes"],
    ]

    def main(self, gmrecords):
        """Process data using steps defined in configuration file.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        # get the process tag from the user or use "default" for tag
        self.process_tag = gmrecords.args.label or "default"
        logging.info(f"Processing tag: {self.process_tag}")

        for event in self.events:
            self._process_event(event)

        self._summarize_files_created()

    def _process_event(self, event):
        self.open_workspace(event.id)
        ds = self.workspace.dataset
        station_list = ds.waveforms.list()

        processed_streams = []
        if self.gmrecords.args.num_processes > 0:
            futures = []

        for station_id in station_list:
            # Cannot parallelize IO to ASDF file
            config = self._get_config()
            raw_streams = self.workspace.getStreams(
                event.id,
                stations=[station_id],
                labels=["unprocessed"],
                config=config,
            )
            if self.gmrecords.args.reprocess:
                # Don't use "processed_streams" variable name because that is what is
                # being used for the result of THIS round of processing; thus, I'm
                # using "old_streams" for the previously processed streams which
                # contain the manually reviewed information
                old_streams = self.workspace.getStreams(
                    event.id,
                    stations=[station_id],
                    labels=[self.process_tag],
                    config=config,
                )
                logging.debug(old_streams.describe())
            else:
                old_streams = None

            if len(raw_streams):
                if self.gmrecords.args.reprocess:
                    process_type = "Reprocessing"
                    plabel = self.process_tag
                else:
                    process_type = "Processing"
                    plabel = "unprocessed"
                logging.info(
                    f"{process_type} '{plabel}' streams for event {event.id}..."
                )
                if self.gmrecords.args.num_processes:
                    with ThreadPoolExecutor(
                        max_workers=self.gmrecords.args.num_processes
                    ) as executor:
                        future = executor.submit(
                            processing.process_streams,
                            raw_streams,
                            event,
                            config,
                            old_streams,
                        )
                        futures.append(future)
                else:
                    processed_streams.append(
                        processing.process_streams(
                            raw_streams, event, config, old_streams
                        )
                    )

        if self.gmrecords.args.num_processes > 0:
            # Collect the processed streams
            processed_streams = [future.result() for future in futures]

        # Cannot parallelize IO to ASDF file
        if self.gmrecords.args.reprocess:
            overwrite = True
        else:
            overwrite = False

        for processed_stream in processed_streams:
            self.workspace.addStreams(
                event,
                processed_stream,
                label=self.process_tag,
                gmprocess_version=self.gmrecords.gmprocess_version,
                overwrite=overwrite,
            )

        self.close_workspace()
        return event.id
