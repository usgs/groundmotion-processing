#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging


from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.fetch_utils import draw_stations_map
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
        ARG_DICTS['label']
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
            self.eventid = event.id
            event_dir = os.path.join(gmrecords.data_path, self.eventid)
            workname = os.path.join(event_dir, WORKSPACE_NAME)
            if not os.path.isfile(workname):
                logging.info(
                    'No workspace file found for event %s. Please run '
                    'subcommand \'assemble\' to generate workspace file.'
                    % self.eventid)
                logging.info('Continuing to next event.')
                continue

            self.workspace = StreamWorkspace.open(workname)
            self._get_pstreams()
            self.workspace.close()

            if not hasattr(self, 'pstreams'):
                logging.info('No processed waveforms available. No report '
                             'generated.')
                return

            logging.info(
                'Creating diagnostic plots for event %s...' % self.eventid)
            plot_dir = os.path.join(event_dir, 'plots')
            if not os.path.isdir(plot_dir):
                os.makedirs(plot_dir)
            for stream in self.pstreams:
                summary_plots(stream, plot_dir, event)

            mapfile = draw_stations_map(self.pstreams, event, event_dir)
            moveoutfile = os.path.join(event_dir, 'moveout_plot.png')
            plot_moveout(self.pstreams, event.latitude, event.longitude,
                         file=moveoutfile)
            self.append_file('Station map', mapfile)
            self.append_file('Moveout plot', moveoutfile)

            logging.info(
                'Generating summary report for event %s...' % self.eventid)

            build_conf = gmrecords.conf['build_report']
            report_format = build_conf['format']
            if report_format == 'latex':
                report_file, success = build_report_latex(
                    self.pstreams,
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
