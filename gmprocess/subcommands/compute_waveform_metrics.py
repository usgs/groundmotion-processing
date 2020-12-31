import os
import logging

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.asdf.stream_workspace import \
    StreamWorkspace, format_netsta, format_nslit
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.utils.constants import WORKSPACE_NAME


class ComputeWaveformMetricsModule(SubcommandModule):
    """Compute waveform metrics.
    """
    command_name = 'compute_waveform_metrics'
    aliases = ('wm', )

    arguments = [
        ARG_DICTS['eventid'],
        ARG_DICTS['label'],
        ARG_DICTS['overwrite']
    ]

    def main(self, gmp):
        """Compute waveform metrics.

        Args:
            gmp: GmpApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        self.gmp = gmp
        self._get_events()

        for event in self.events:
            self.eventid = event.id
            logging.info(
                'Computing waveform metrics for event %s...' % self.eventid)
            event_dir = os.path.join(gmp.data_path, self.eventid)
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

            for stream in self.pstreams:
                logging.info(
                    'Calculating waveform metrics for %s...' % stream.get_id())
                summary = StationSummary.from_config(
                    stream, event=event, config=gmp.conf,
                    calc_waveform_metrics=True,
                    calc_station_metrics=False)
                xmlstr = summary.get_metric_xml()
                tag = stream.tag
                metricpath = '/'.join([
                    format_netsta(stream[0].stats),
                    format_nslit(stream[0].stats, stream.get_inst(), tag)
                ])
                self.workspace.insert_aux(
                    xmlstr, 'WaveFormMetrics', metricpath,
                    overwrite=gmp.args.overwrite)

            self.workspace.close()

        logging.info('Added waveform metrics to workspace files '
                     'with tag \'%s\'.' % self.gmp.args.label)
        self._summarize_files_created()
