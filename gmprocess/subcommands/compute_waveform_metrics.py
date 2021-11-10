#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

from dask.distributed import Client

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
        ARG_DICTS['textfile'],
        ARG_DICTS['label'],
        ARG_DICTS['overwrite'],
        ARG_DICTS['num_processes']
    ]

    def main(self, gmrecords):
        """Compute waveform metrics.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        for event in self.events:
            self._compute_event_waveform_metrics(event)

        self._summarize_files_created()

    def _compute_event_waveform_metrics(self, event):
        self.eventid = event.id
        logging.info(
            'Computing waveform metrics for event %s...' % self.eventid)
        event_dir = os.path.join(self.gmrecords.data_path, self.eventid)
        workname = os.path.normpath(os.path.join(event_dir, WORKSPACE_NAME))
        if not os.path.isfile(workname):
            logging.info(
                'No workspace file found for event %s. Please run '
                'subcommand \'assemble\' to generate workspace file.'
                % self.eventid)
            logging.info('Continuing to next event.')
            return event.id

        self.workspace = StreamWorkspace.open(workname)
        ds = self.workspace.dataset
        station_list = ds.waveforms.list()
        self._get_labels()

        summaries = []
        metricpaths = []
        if self.gmrecords.args.num_processes > 0:
            futures = []
            client = Client(n_workers=self.gmrecords.args.num_processes)

        for station_id in station_list:
            # Cannot parallelize IO to ASDF file
            stream = self.workspace.getStreams(
                event.id,
                stations=[station_id],
                labels=[self.gmrecords.args.label],
                config=self.gmrecords.conf
            )[0]

            if stream.passed:
                metricpaths.append('/'.join([
                    format_netsta(stream[0].stats),
                    format_nslit(
                        stream[0].stats,
                        stream.get_inst(),
                        stream.tag)
                ]))
                logging.info(
                    'Calculating waveform metrics for %s...'
                    % stream.get_id()
                )
                if self.gmrecords.args.num_processes > 0:
                    future = client.submit(
                        StationSummary.from_config,
                        stream=stream,
                        config=self.gmrecords.conf,
                        event=event,
                        calc_waveform_metrics=True,
                        calc_station_metrics=False)
                    futures.append(future)
                else:
                    summaries.append(
                        StationSummary.from_config(
                            stream, event=event,
                            config=self.gmrecords.conf,
                            calc_waveform_metrics=True,
                            calc_station_metrics=False
                        )
                    )

        if self.gmrecords.args.num_processes > 0:
            # Collect the processed streams
            summaries = [future.result() for future in futures]
            client.shutdown()

        # Cannot parallelize IO to ASDF file
        logging.info('Adding waveform metrics to workspace files '
                     'with tag \'%s\'.' % self.gmrecords.args.label)
        for i, summary in enumerate(summaries):
            xmlstr = summary.get_metric_xml()
            metricpath = metricpaths[i]
            self.workspace.insert_aux(
                xmlstr, 'WaveFormMetrics', metricpath,
                overwrite=self.gmrecords.args.overwrite)

        self.workspace.close()
        return event.id
