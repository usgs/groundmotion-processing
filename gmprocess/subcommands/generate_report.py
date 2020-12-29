import os
import sys
import logging


from gmprocess.subcommands.base import SubcommandModule
from gmprocess.io.fetch_utils import get_events, draw_stations_map
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.report import build_report_latex
from gmprocess.utils.constants import DEFAULT_FLOAT_FORMAT, DEFAULT_NA_REP
from gmprocess.utils.plot import summary_plots, plot_moveout


class GenerateReportModule(SubcommandModule):
    """Generate summary report (latex required).
    """
    command_name = 'generate_report'
    aliases = ('report', )

    arguments = [
        {
            'short_flag': '-e',
            'long_flag': '--eventid',
            'help': ('Comcat event ID. If None (default) all events in '
                     'project data directory will be used.'),
            'type': str,
            'default': None,
            'nargs': '+'
        }
    ]

    def main(self, gmp):
        """Generate summary report.

        This function generates summary plots and then combines them into a
        report with latex. If latex (specifically `pdflatex`) is not found on
        the system then the PDF report will not be generated but the
        constituent plots will be available.

        Args:
            gmp: GmpApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        events = get_events(
            eventids=gmp.args.eventid,
            textfile=None,
            eventinfo=None,
            directory=gmp.data_path,
            outdir=None
        )

        label = None

        for event in events:
            event_dir = os.path.join(gmp.data_path, event.id)
            workname = os.path.join(event_dir, 'workspace.hdf')
            if not os.path.isfile(workname):
                logging.info(
                    'No workspace file found for event %s. Please run '
                    'subcommand \'assemble\' to generate workspace file.'
                    % event.id)
                logging.info('Continuing to next event.')
                continue
            workspace = StreamWorkspace.open(workname)
            labels = workspace.getLabels()

            if len(labels) > 1 and 'unprocessed' in labels:
                labels.remove('unprocessed')
            else:
                logging.info('No processed waveform data in workspace. Please '
                             'run assemble.')
                sys.exit(1)

            # If there are more than 1 processed labels, prompt user to select
            # one.
            if len(labels) > 1 and label is not None:
                print('Which label do you want to use?')
                for lab in labels:
                    print('\t%s' % lab)
                tmplab = input()
                if tmplab not in labels:
                    raise ValueError('%s not a valid label. Exiting.' % tmplab)
                else:
                    label = tmplab
            else:
                label = labels[0]

            pstreams = workspace.getStreams(
                event.id, labels=[label])
            workspace.close()

            logging.info(
                'Creating diagnostic plots for event %s...' % event.id)
            plot_dir = os.path.join(event_dir, 'plots')
            if not os.path.isdir(plot_dir):
                os.makedirs(plot_dir)
            for stream in pstreams:
                summary_plots(stream, plot_dir, event)

            mapfile = draw_stations_map(pstreams, event, event_dir)
            moveoutfile = os.path.join(event_dir, 'moveout_plot.png')
            plot_moveout(pstreams, event.latitude, event.longitude,
                         file=moveoutfile)
            self.append_file('Station map', mapfile)
            self.append_file('Moveout plot', moveoutfile)

            logging.info(
                'Generating summary report for event %s...' % event.id)

            build_conf = gmp.conf['build_report']
            report_format = build_conf['format']
            if report_format == 'latex':
                report_file, success = build_report_latex(
                    pstreams,
                    event_dir,
                    event,
                    config=gmp.conf
                )
            else:
                report_file = ''
                success = False
            if os.path.isfile(report_file) and success:
                self.append_file('Summary report', report_file)

        self._summarize_files_created()
