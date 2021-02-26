#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging

from dask.distributed import Client, as_completed

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

        if gmrecords.args.num_processes:
            # parallelize processing on events
            try:
                client = Client(n_workers=gmrecords.args.num_processes)
            except BaseException as ex:
                print(ex)
                print("Could not create a dask client.")
                print("To turn off paralleization, use '--num-processes 0'.")
                sys.exit(1)
            futures = client.map(self._compute_event_waveforms, self.events)
            for result in as_completed(futures, with_results=True):
                print(result)
        else:
            for event in self.events:
                self._compute_event_waveforms(event)

        self._summarize_files_created()

    def _compute_event_waveforms(self, event):
        self.eventid = event.id
        logging.info(
            'Computing waveform metrics for event %s...' % self.eventid)
        event_dir = os.path.join(self.gmrecords.data_path, self.eventid)
        workname = os.path.join(event_dir, WORKSPACE_NAME)
        if not os.path.isfile(workname):
            logging.info(
                'No workspace file found for event %s. Please run '
                'subcommand \'assemble\' to generate workspace file.'
                % self.eventid)
            logging.info('Continuing to next event.')
            return event.id

        self.workspace = StreamWorkspace.open(workname)
        self._get_pstreams()

        if not hasattr(self, 'pstreams'):
            logging.info('No streams found. Nothing to do. Goodbye.')
            return event.id

        if not hasattr(self, 'pstreams'):
            logging.info('No processed waveforms available. No waveform '
                         'metrics computed.')
            self.workspace.close()
            return event.id

        for stream in self.pstreams:
            if stream.passed:
                logging.info(
                    'Calculating waveform metrics for %s...'
                    % stream.get_id()
                )
                summary = StationSummary.from_config(
                    stream, event=event, config=self.gmrecords.conf,
                    calc_waveform_metrics=True,
                    calc_station_metrics=False
                )
                xmlstr = summary.get_metric_xml()
                tag = stream.tag
                metricpath = '/'.join([
                    format_netsta(stream[0].stats),
                    format_nslit(stream[0].stats, stream.get_inst(), tag)
                ])
                self.workspace.insert_aux(
                    xmlstr, 'WaveFormMetrics', metricpath,
                    overwrite=self.gmrecords.args.overwrite)
            logging.info('Added waveform metrics to workspace files '
                         'with tag \'%s\'.' % self.gmrecords.args.label)

        self.workspace.close()
        return event.id
