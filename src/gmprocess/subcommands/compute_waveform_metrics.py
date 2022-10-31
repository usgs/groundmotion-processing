#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from concurrent.futures import ProcessPoolExecutor

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

    arguments = []

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

        for ievent, event in enumerate(self.events):
            logging.info(
                f"Computing waveform metrics for event {event.id} "
                f"({1+ievent} of {len(self.events)})..."
            )
            self._compute_event_waveform_metrics(event)

        self._summarize_files_created()

    def _compute_event_waveform_metrics(self, event):
        self.eventid = event.id
        event_dir = self.gmrecords.data_path / self.eventid
        workname = event_dir / const.WORKSPACE_NAME
        if not workname.is_file():
            logging.info(
                "No workspace file found for event {self.eventid}. Please run "
                "subcommand 'assemble' to generate workspace file."
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
            executor = ProcessPoolExecutor(
                max_workers=self.gmrecords.args.num_processes
            )

        for station_id in station_list:
            # Cannot parallelize IO to ASDF file
            streams = self.workspace.getStreams(
                event.id,
                stations=[station_id],
                labels=[self.gmrecords.args.label],
                config=config,
            )
            if not len(streams):
                logging.warning(
                    "No matching streams found. Aborting computation of station "
                    f"metrics for {station_id} for {event.id}."
                )
                continue

            for stream in streams:
                if not stream.passed:
                    continue
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
                logging.info(f"Calculating waveform metrics for {stream.get_id()}...")
                if self.gmrecords.args.num_processes > 0:
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

        if self.gmrecords.args.num_processes:
            # Collect the processed streams
            summaries = [future.result() for future in futures]
            executor.shutdown()

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
