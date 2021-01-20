#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

from mapio.gmt import GMTGrid
from impactutils.rupture.origin import Origin

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.fetch_utils import get_rupture_file
from impactutils.rupture.factory import get_rupture
from gmprocess.io.asdf.stream_workspace import \
    StreamWorkspace, format_netsta, format_nslit
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.utils.constants import WORKSPACE_NAME


class ComputeStationMetricsModule(SubcommandModule):
    """Compute station metrics.
    """
    command_name = 'compute_station_metrics'
    aliases = ('sm', )

    arguments = [
        ARG_DICTS['eventid'],
        ARG_DICTS['label'],
        ARG_DICTS['overwrite']
    ]

    def main(self, gmrecords):
        """Compute station metrics.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        self.gmrecords = gmrecords
        self._get_events()

        vs30_grids = None
        if gmrecords.conf is not None:
            if 'vs30' in gmrecords.conf['metrics']:
                vs30_grids = gmrecords.conf['metrics']['vs30']
                for vs30_name in vs30_grids:
                    vs30_grids[vs30_name]['grid_object'] = GMTGrid.load(
                        vs30_grids[vs30_name]['file'])

        for event in self.events:
            self.eventid = event.id
            logging.info('Computing station metrics for event %s...'
                         % self.eventid)
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

            rupture_file = get_rupture_file(event_dir)
            origin = Origin({
                'id': self.eventid,
                'netid': '',
                'network': '',
                'lat': event.latitude,
                'lon': event.longitude,
                'depth': event.depth_km,
                'locstring': '',
                'mag': event.magnitude,
                'time': event.time
            })
            rupture = get_rupture(origin, rupture_file)

            if not hasattr(self, 'pstreams'):
                logging.info('No processed waveforms available. No station '
                             'metrics computed.')
                self.workspace.close()
                return

            for stream in self.pstreams:
                logging.info(
                    'Calculating station metrics for %s...' % stream.get_id())
                summary = StationSummary.from_config(
                    stream, event=event, config=gmrecords.conf,
                    calc_waveform_metrics=False,
                    calc_station_metrics=True,
                    rupture=rupture, vs30_grids=vs30_grids)
                xmlstr = summary.get_station_xml()
                metricpath = '/'.join([
                    format_netsta(stream[0].stats),
                    format_nslit(
                        stream[0].stats,
                        stream.get_inst(),
                        self.eventid)
                ])
                self.workspace.insert_aux(
                    xmlstr, 'StationMetrics', metricpath,
                    overwrite=gmrecords.args.overwrite)
                logging.info('Added station metrics to workspace files '
                             'with tag \'%s\'.' % self.gmrecords.args.label)

            self.workspace.close()

        self._summarize_files_created()
