#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from gmprocess.subcommands.lazy_loader import LazyLoader

base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
download = LazyLoader("download", globals(), "gmprocess.subcommands.download")
assemble = LazyLoader("assemble", globals(), "gmprocess.subcommands.assemble")
process_waveforms = LazyLoader(
    "process_waveforms", globals(), "gmprocess.subcommands.process_waveforms"
)
compute_station_metrics = LazyLoader(
    "compute_station_metrics",
    globals(),
    "gmprocess.subcommands.compute_station_metrics",
)
compute_waveform_metrics = LazyLoader(
    "compute_waveform_metrics",
    globals(),
    "gmprocess.subcommands.compute_waveform_metrics",
)
generate_report = LazyLoader(
    "generate_report", globals(), "gmprocess.subcommands.generate_report"
)
generate_station_maps = LazyLoader(
    "generate_station_maps", globals(), "gmprocess.subcommands.generate_station_maps"
)


class AutoShakemapModule(base.SubcommandModule):
    """Chain together the most common processing subcommands."""

    epilog = """
    This is a convenience function, but it also provides a mechanism to loop over
    events, calling each of the following subcommands in order:
      - download
      - assemble
      - process_waveforms
      - compute_station_metrics
      - compute_waveform_metrics
      - generate_report
      - generate_station_maps
    Individual subcommands can be turned off with the arguments to this subcommand.
    """
    command_name = "autoprocess"

    arguments = [
        {
            "long_flag": "--no-download",
            "help": "Skip download subcommand.",
            "default": False,
            "action": "store_true",
        },
        {
            "long_flag": "--no-assemble",
            "help": "Skip assemble subcommand.",
            "default": False,
            "action": "store_true",
        },
        {
            "long_flag": "--no-process",
            "help": "Skip process_waveforms subcommand.",
            "default": False,
            "action": "store_true",
        },
        {
            "long_flag": "--no-station_metrics",
            "help": "Skip compute_station_metrics subcommand.",
            "default": False,
            "action": "store_true",
        },
        {
            "long_flag": "--no-waveform_metrics",
            "help": "Skip compute_waveform_metrics subcommand.",
            "default": False,
            "action": "store_true",
        },
        {
            "long_flag": "--no-report",
            "help": "Skip generate_report subcommand.",
            "default": False,
            "action": "store_true",
        },
        {
            "long_flag": "--no-maps",
            "help": "Skip generate_station_maps subcommand.",
            "default": False,
            "action": "store_true",
        },
    ]

    def main(self, gmrecords):
        """Chain together the most common processing subcommands."""
        logging.info(f"Running subcommand '{self.command_name}'")
        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()
        nevents = len(self.events)

        for ievent, event in enumerate(self.events):
            logging.info(
                f"(auto)processing event {event.id} ({1+ievent} of {nevents})..."
            )
            # stomp on gmrecords.args.eventid
            gmrecords.args.eventid = [event.id]

            # Chain together relevant subcommand modules:
            if not gmrecords.args.no_download:
                download.DownloadModule().main(gmrecords)
            if not gmrecords.args.no_assemble:
                assemble.AssembleModule().main(gmrecords)
            if not gmrecords.args.no_process:
                process_waveforms.ProcessWaveformsModule().main(gmrecords)
            if not gmrecords.args.no_station_metrics:
                compute_station_metrics.ComputeStationMetricsModule().main(gmrecords)
            if not gmrecords.args.no_waveform_metrics:
                compute_waveform_metrics.ComputeWaveformMetricsModule().main(gmrecords)
            if not gmrecords.args.no_report:
                generate_report.GenerateReportModule().main(gmrecords)
            if not gmrecords.args.no_maps:
                generate_station_maps.GenerateHTMLMapModule().main(gmrecords)
