#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

from dask.distributed import Client

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.utils.report_utils import draw_stations_map
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.report import build_report_latex
from gmprocess.utils.plot import summary_plots, plot_moveout
from gmprocess.utils.constants import WORKSPACE_NAME


class GenerateReportModule(SubcommandModule):
    """Generate summary report (latex required).
    """
    command_name = 'generate_report'
    aliases = ('report', )

    arguments = [
        ARG_DICTS['eventid'],
        ARG_DICTS['textfile'],
        ARG_DICTS['label'],
        ARG_DICTS['num_processes']
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
        logging.info('Running subcommand \'%s\'' % self.command_name)

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        for event in self.events:
            event_dir = os.path.join(self.gmrecords.data_path, event.id)
            pstreams = self.generate_diagnostic_plots(event)

            logging.info(
                'Generating summary report for event %s...' % event.id)

            build_conf = gmrecords.conf['build_report']
            report_format = build_conf['format']
            if report_format == 'latex':
                report_file, success = build_report_latex(
                    pstreams,
                    event_dir,
                    event,
                    prefix="%s_%s" % (gmrecords.project, gmrecords.args.label),
                    config=gmrecords.conf
                )
            else:
                report_file = ''
                success = False
            if os.path.isfile(report_file) and success:
                self.append_file('Summary report', report_file)

        self._summarize_files_created()

    def generate_diagnostic_plots(self, event):
        event_dir = os.path.join(self.gmrecords.data_path, event.id)
        workname = os.path.join(event_dir, WORKSPACE_NAME)
        if not os.path.isfile(workname):
            logging.info(
                'No workspace file found for event %s. Please run '
                'subcommand \'assemble\' to generate workspace file.'
                % event.id)
            logging.info('Continuing to next event.')
            return False

        self.workspace = StreamWorkspace.open(workname)
        ds = self.workspace.dataset
        station_list = ds.waveforms.list()
        self._get_labels()

        if len(station_list) == 0:
            logging.info('No processed waveforms available. No report '
                         'generated.')
            return False

        if self.gmrecords.args.num_processes > 0:
            futures = []
            client = Client(n_workers=self.gmrecords.args.num_processes)

        logging.info('Creating diagnostic plots for event %s...' % event.id)
        plot_dir = os.path.join(event_dir, 'plots')
        if not os.path.isdir(plot_dir):
            os.makedirs(plot_dir)

        results = []
        pstreams = []
        for station_id in station_list:
            stream = self.workspace.getStreams(
                event.id,
                stations=[station_id],
                labels=[self.gmrecords.args.label],
                config=self.gmrecords.conf
            )[0]
            pstreams.append(stream)
            if self.gmrecords.args.num_processes > 0:
                future = client.submit(summary_plots, stream, plot_dir, event)
                futures.append(future)
            else:
                results.append(summary_plots(stream, plot_dir, event))

        if self.gmrecords.args.num_processes > 0:
            # Collect the results??
            results = [future.result() for future in futures]
            client.shutdown()

        mapfile = draw_stations_map(pstreams, event, event_dir)
        moveoutfile = os.path.join(event_dir, 'moveout_plot.png')
        plot_moveout(pstreams, event.latitude, event.longitude,
                     file=moveoutfile)
        self.append_file('Station map', mapfile)
        self.append_file('Moveout plot', moveoutfile)

        self.workspace.close()

        return pstreams
