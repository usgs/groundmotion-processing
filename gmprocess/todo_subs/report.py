import logging

from gmprocess.commands.base import CoreModule
from gmprocess.io.report import build_report_latex
from gmprocess.utils.plot import summary_plots, plot_regression, plot_moveout


class ReportModule(CoreModule):
    """
    Create a summary report for each event specified.
    """
    command_name = 'report'

    def __init__(self, eventid):
        pass

    def execute(self):
        """
        """
        logging.info(
            'Creating diagnostic plots for event %s...' % event.id)
        plot_dir = os.path.join(event_dir, 'plots')
        if not os.path.isdir(plot_dir):
            os.makedirs(plot_dir)
        for stream in pstreams:
            summary_plots(stream, plot_dir, event)

        mapfile = draw_stations_map(pstreams, event, event_dir)
        plot_moveout(pstreams, event.latitude, event.longitude,
                     file=os.path.join(event_dir, 'moveout_plot.png'))

        append_file(files_created, 'Station map', mapfile)
        append_file(files_created, 'Moveout plot', 'moveout_plot.png')

        logging.info(
            'Creating diagnostic report for event %s...' % event.id)
        # Build the summary report?
        build_conf = config['build_report']
        report_format = build_conf['format']
        if report_format == 'latex':
            report_file, success = build_report_latex(
                pstreams,
                event_dir,
                event,
                config=config
            )
        else:
            report_file = ''
            success = False
        if os.path.isfile(report_file) and success:
            append_file(files_created, 'Summary report', report_file)
