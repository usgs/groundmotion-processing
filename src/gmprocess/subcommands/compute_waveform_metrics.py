#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from concurrent.futures import ThreadPoolExecutor

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
station_summary = LazyLoader(
    "station_summary", globals(), "gmprocess.metrics.station_summary"
)
const = LazyLoader("const", globals(), "gmprocess.utils.constants")
confmod = LazyLoader("confmod", globals(), "gmprocess.utils.config")


class ComputeWaveformMetricsModule(base.SubcommandModule):
    """Compute waveform metrics."""

    command_name = "compute_waveform_metrics"
    aliases = ("wm",)

    arguments = [
        arg_dicts.ARG_DICTS["eventid"],
        arg_dicts.ARG_DICTS["textfile"],
        arg_dicts.ARG_DICTS["label"],
        arg_dicts.ARG_DICTS["overwrite"],
        arg_dicts.ARG_DICTS["num_processes"],
    ]

    def main(self, gmrecords):
        """Compute waveform metrics.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        for event in self.events:
            self._compute_event_waveform_metrics(event)

        self._summarize_files_created()

    def _compute_event_waveform_metrics(self, event):
        self.eventid = event.id
        logging.info(f"Computing waveform metrics for event {self.eventid}...")
        event_dir = os.path.join(self.gmrecords.data_path, self.eventid)
        workname = os.path.normpath(os.path.join(event_dir, const.WORKSPACE_NAME))
        if not os.path.isfile(workname):
            logging.info(
                "No workspace file found for event %s. Please run "
                "subcommand 'assemble' to generate workspace file." % self.eventid
            )
            logging.info("Continuing to next event.")
            return event.id

        self.workspace = ws.StreamWorkspace.open(workname)
        ds = self.workspace.dataset
        station_list = ds.waveforms.list()
        self._get_labels()
        config = self._get_config()

        summaries = []
        metricpaths = []
        if self.gmrecords.args.num_processes:
            futures = []

        for station_id in station_list:
            # Cannot parallelize IO to ASDF file
            streams = self.workspace.getStreams(
                event.id,
                stations=[station_id],
                labels=[self.gmrecords.args.label],
                config=config,
            )
            if not len(streams):
                raise ValueError("No matching streams found.")

            for stream in streams:
                if stream.passed:
                    if config["read"]["use_streamcollection"]:
                        chancode = stream.get_inst()
                    else:
                        chancode = stream[0].stats.channel
                    metricpaths.append(
                        "/".join(
                            [
                                ws.format_netsta(stream[0].stats),
                                ws.format_nslit(stream[0].stats, chancode, stream.tag),
                            ]
                        )
                    )
                    logging.info(
                        f"Calculating waveform metrics for {stream.get_id()}..."
                    )
                    if self.gmrecords.args.num_processes > 0:
                        with ThreadPoolExecutor(
                            max_workers=self.gmrecords.args.num_processes
                        ) as executor:
                            future = executor.submit(
                                station_summary.StationSummary.from_config,
                                stream=stream,
                                config=config,
                                event=event,
                                calc_waveform_metrics=True,
                                calc_station_metrics=False,
                            )
                            futures.append(future)
                    else:
                        summaries.append(
                            station_summary.StationSummary.from_config(
                                stream,
                                event=event,
                                config=config,
                                calc_waveform_metrics=True,
                                calc_station_metrics=False,
                            )
                        )

        if self.gmrecords.args.num_processes > 0:
            # Collect the processed streams
            summaries = [future.result() for future in futures]

        # Cannot parallelize IO to ASDF file
        logging.info(
            "Adding waveform metrics to workspace files "
            "with tag '%s'." % self.gmrecords.args.label
        )
        for i, summary in enumerate(summaries):
            xmlstr = summary.get_metric_xml()
            metricpath = metricpaths[i]
            self.workspace.insert_aux(
                xmlstr,
                "WaveFormMetrics",
                metricpath,
                overwrite=self.gmrecords.args.overwrite,
            )

        self.workspace.close()
        return event.id
