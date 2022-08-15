#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from concurrent.futures import ThreadPoolExecutor

from gmprocess.subcommands.lazy_loader import LazyLoader


base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
report = LazyLoader("report", globals(), "gmprocess.io.report")
plot = LazyLoader("plot", globals(), "gmprocess.utils.plot")
const = LazyLoader("const", globals(), "gmprocess.utils.constants")


class GenerateReportModule(base.SubcommandModule):
    """Generate summary report (latex required)."""

    command_name = "generate_report"
    aliases = ("report",)

    arguments = [
        arg_dicts.ARG_DICTS["eventid"],
        arg_dicts.ARG_DICTS["textfile"],
        arg_dicts.ARG_DICTS["label"],
        arg_dicts.ARG_DICTS["num_processes"],
    ]

    def main(self, gmrecords):
        """Generate summary report.

        This function generates summary plots and then combines them into a
        report with latex. If latex (specifically `pdflatex`) is not found on
        the system then the PDF report will not be generated but the
        constituent plots will be available.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        for event in self.events:
            event_dir = os.path.join(self.gmrecords.data_path, event.id)
            pstreams = self.generate_diagnostic_plots(event)
            if pstreams is None:
                return

            logging.info(f"Generating summary report for event {event.id}...")

            config = self._get_config()
            build_conf = config["build_report"]
            if build_conf["enabled"]:
                report_format = build_conf["format"]
                if report_format == "latex":
                    report_file, success = report.build_report_latex(
                        pstreams,
                        event_dir,
                        event,
                        prefix=f"{gmrecords.project}_{gmrecords.args.label}",
                        config=config,
                        gmprocess_version=gmrecords.gmprocess_version,
                    )
                else:
                    report_file = ""
                    success = False
                if os.path.isfile(report_file) and success:
                    self.append_file("Summary report", report_file)

        self._summarize_files_created()

    def generate_diagnostic_plots(self, event):
        event_dir = os.path.join(self.gmrecords.data_path, event.id)
        workname = os.path.join(event_dir, const.WORKSPACE_NAME)
        if not os.path.isfile(workname):
            logging.info(
                "No workspace file found for event %s. Please run "
                "subcommand 'assemble' to generate workspace file." % event.id
            )
            logging.info("Continuing to next event.")
            return False

        self.workspace = ws.StreamWorkspace.open(workname)
        config = self._get_config()
        ds = self.workspace.dataset
        station_list = ds.waveforms.list()
        if len(station_list) == 0:
            logging.info("No processed waveforms available. No report generated.")
            return []

        self._get_labels()
        if self.gmrecords.args.num_processes:
            futures = []

        logging.info(f"Creating diagnostic plots for event {event.id}...")
        plot_dir = os.path.join(event_dir, "plots")
        if not os.path.isdir(plot_dir):
            os.makedirs(plot_dir)

        results = []
        pstreams = []
        for station_id in station_list:
            streams = self.workspace.getStreams(
                event.id,
                stations=[station_id],
                labels=[self.gmrecords.args.label],
                config=config,
            )
            if not len(streams):
                logging.info("No matching streams found. Cannot generate report.")
                return

            for stream in streams:
                pstreams.append(stream)
                if self.gmrecords.args.num_processes > 0:
                    with ThreadPoolExecutor(
                        max_workers=self.gmrecords.args.num_processes
                    ) as executor:
                        future = executor.submit(
                            plot.summary_plots,
                            stream,
                            plot_dir,
                            event,
                            config=config,
                        )
                        futures.append(future)
                else:
                    results.append(
                        plot.summary_plots(stream, plot_dir, event, config=config)
                    )

        if self.gmrecords.args.num_processes > 0:
            # Collect the results??
            results = [future.result() for future in futures]

        moveoutfile = os.path.join(event_dir, "moveout_plot.png")
        plot.plot_moveout(pstreams, event.latitude, event.longitude, file=moveoutfile)
        self.append_file("Moveout plot", moveoutfile)

        self.workspace.close()

        return pstreams
