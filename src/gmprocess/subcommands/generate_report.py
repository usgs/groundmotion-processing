#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import shutil
from concurrent.futures import ProcessPoolExecutor

from gmprocess.subcommands.lazy_loader import LazyLoader


base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
report = LazyLoader("report", globals(), "gmprocess.io.report")
plot = LazyLoader("plot", globals(), "gmprocess.utils.plot")
const = LazyLoader("const", globals(), "gmprocess.utils.constants")


class GenerateReportModule(base.SubcommandModule):
    """Generate summary report (latex required)."""

    command_name = "generate_report"
    aliases = ("report",)

    arguments = []

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

        for ievent, event in enumerate(self.events):
            event_dir = self.gmrecords.data_path / event.id
            pstreams = self.generate_diagnostic_plots(event)
            if pstreams is None:
                return

            logging.info(
                f"Generating summary report for event {event.id} "
                f"({1+ievent} of {len(self.events)})..."
            )

            config = self._get_config()
            build_conf = config["build_report"]
            if build_conf["enabled"]:
                report_format = build_conf["format"]
                if report_format == "latex":
                    report_file, success = report.build_report_latex(
                        pstreams,
                        event_dir,
                        event,
                        prefix=f"{gmrecords.project_name}_{gmrecords.args.label}",
                        config=config,
                        gmprocess_version=gmrecords.gmprocess_version,
                    )
                else:
                    report_file = ""
                    success = False
                if report_file.is_file() and success:
                    self.append_file("Summary report", report_file)

        self._summarize_files_created()

    def generate_diagnostic_plots(self, event):
        event_dir = self.gmrecords.data_path / event.id
        workname = event_dir / const.WORKSPACE_NAME
        if not workname.is_file():
            logging.info(
                f"No workspace file found for event {event.id}. Please run "
                "subcommand 'assemble' to generate workspace file."
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
            executor = ProcessPoolExecutor(
                max_workers=self.gmrecords.args.num_processes
            )

        logging.info(f"Creating diagnostic plots for event {event.id}...")
        plot_dir = event_dir / "plots"

        if plot_dir.exists():
            shutil.rmtree(plot_dir, ignore_errors=True)
        plot_dir.mkdir()

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

        if self.gmrecords.args.num_processes:
            # Collect the results??
            results = [future.result() for future in futures]
            executor.shutdown()

        moveoutfile = event_dir / "moveout_plot.png"
        plot.plot_moveout(pstreams, event.latitude, event.longitude, file=moveoutfile)
        self.append_file("Moveout plot", moveoutfile)

        self.workspace.close()

        return pstreams
