#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from gmprocess.subcommands.lazy_loader import LazyLoader

base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
const = LazyLoader("const", globals(), "gmprocess.utils.constants")
report_utils = LazyLoader("report_utils", globals(), "gmprocess.utils.report_utils")


class GenerateHTMLMapModule(base.SubcommandModule):
    """Generate interactive station maps."""

    command_name = "generate_station_maps"
    aliases = ("maps",)

    arguments = []

    def main(self, gmrecords):
        """Generate summary report.

        This function generates station map.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        for ievent, event in enumerate(self.events):
            event_dir = self.gmrecords.data_path / event.id
            workname = event_dir / const.WORKSPACE_NAME
            if not workname.is_file():
                logging.error(
                    f"No workspace file found for event {event.id}. Please run "
                    "subcommand 'assemble' to generate workspace file."
                    "Continuing to next event."
                )
                continue

            self.workspace = ws.StreamWorkspace.open(workname)
            ds = self.workspace.dataset
            station_list = ds.waveforms.list()
            if len(station_list) == 0:
                logging.info("No processed waveforms available. No report generated.")
                continue

            self._get_labels()
            config = self.workspace.config
            logging.info(
                f"Generating station maps for event {event.id} "
                f"({1+ievent} of {len(self.events)})..."
            )

            pstreams = []
            for station_id in station_list:
                streams = self.workspace.getStreams(
                    event.id,
                    stations=[station_id],
                    labels=[self.gmrecords.args.label],
                    config=config,
                )
                if not len(streams):
                    logging.error(
                        "No matching streams found for {station_id} for {event.id}."
                    )
                    continue

                for stream in streams:
                    pstreams.append(stream)

            mapfile = report_utils.draw_stations_map(pstreams, event, event_dir)
            self.append_file("Station map", mapfile)

        self._summarize_files_created()
