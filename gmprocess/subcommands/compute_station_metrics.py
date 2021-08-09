#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import numpy as np
import scipy.interpolate as spint

from mapio.gmt import GMTGrid
from obspy.geodetics.base import gps2dist_azimuth
from openquake.hazardlib.geo.geodetic import distance
from impactutils.rupture.origin import Origin
from impactutils.rupture.factory import get_rupture
from impactutils.rupture.point_rupture import PointRupture
from ps2ff.constants import MagScaling, Mechanism
from ps2ff.run import single_event_adjustment

from dask.distributed import Client, as_completed

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.fetch_utils import get_rupture_file
from gmprocess.io.asdf.stream_workspace import \
    StreamWorkspace, format_netsta, format_nslit
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.utils.constants import WORKSPACE_NAME
from gmprocess.utils.constants import ELEVATION_FOR_DISTANCE_CALCS

M_PER_KM = 1000


class ComputeStationMetricsModule(SubcommandModule):
    """Compute station metrics.
    """
    command_name = 'compute_station_metrics'
    aliases = ('sm', )

    arguments = [
        ARG_DICTS['eventid'],
        ARG_DICTS['textfile'],
        ARG_DICTS['label'],
        ARG_DICTS['overwrite'],
        ARG_DICTS['num_processes']
    ]

    def main(self, gmrecords):
        """Compute station metrics.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        vs30_grids = None
        if gmrecords.conf is not None:
            if 'vs30' in gmrecords.conf['metrics']:
                vs30_grids = gmrecords.conf['metrics']['vs30']
                for vs30_name in vs30_grids:
                    vs30_grids[vs30_name]['grid_object'] = GMTGrid.load(
                        vs30_grids[vs30_name]['file'])
        self.vs30_grids = vs30_grids

        if gmrecords.args.num_processes:
            # parallelize processing on events
            try:
                client = Client(n_workers=gmrecords.args.num_processes)
            except BaseException as ex:
                print(ex)
                print("Could not create a dask client.")
                print("To turn off paralleization, use '--num-processes 0'.")
                sys.exit(1)
            futures = client.map(self._event_station_metrics, self.events)
            for result in as_completed(futures, with_results=True):
                print(result)
                # print('Completed event: %s' % result)
        else:
            for event in self.events:
                self._event_station_metrics(event)

        self._summarize_files_created()

    def _event_station_metrics(self, event):
        self.eventid = event.id
        logging.info('Computing station metrics for event %s...'
                     % self.eventid)
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

        if not (hasattr(self, 'pstreams') and len(self.pstreams) > 0):
            logging.info('No streams found. Nothing to do. Goodbye.')
            self.workspace.close()
            return event.id

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
        self.origin = origin
        rupture = get_rupture(origin, rupture_file)

        sta_lats = []
        sta_lons = []
        sta_elev = []
        self.sta_repi = []
        self.sta_rhyp = []
        self.sta_baz = []
        for st in self.pstreams:
            sta_lats.append(st[0].stats.coordinates.latitude)
            sta_lons.append(st[0].stats.coordinates.longitude)
            sta_elev.append(st[0].stats.coordinates.elevation)
            geo_tuple = gps2dist_azimuth(
                st[0].stats.coordinates.latitude,
                st[0].stats.coordinates.longitude,
                origin.lat, origin.lon)
            self.sta_repi.append(geo_tuple[0] / M_PER_KM)
            self.sta_baz.append(geo_tuple[1])
            self.sta_rhyp.append(
                distance(st[0].stats.coordinates.longitude,
                         st[0].stats.coordinates.latitude,
                         -st[0].stats.coordinates.elevation / M_PER_KM,
                         origin.lon, origin.lat, origin.depth)
            )

        if isinstance(rupture, PointRupture):
            self._get_ps2ff_splines()
            rjb_hat = self.rjb_spline(self.sta_repi)
            rjb_mean = rjb_hat[0]
            rjb_var = rjb_hat[1]
            rrup_hat = self.rrup_spline(self.sta_repi)
            rrup_mean = rrup_hat[0]
            rrup_var = rrup_hat[1]
            gc2_rx = np.full_like(rjb_mean, np.nan)
            gc2_ry = np.full_like(rjb_mean, np.nan)
            gc2_ry0 = np.full_like(rjb_mean, np.nan)
            gc2_U = np.full_like(rjb_mean, np.nan)
            gc2_T = np.full_like(rjb_mean, np.nan)
        else:
            logging.info('******************************')
            logging.info('* Found rupture              *')
            logging.info('******************************')
            sta_lons = np.array(sta_lons)
            sta_lats = np.array(sta_lats)
            elev = np.full_like(sta_lons, ELEVATION_FOR_DISTANCE_CALCS)
            rrup_mean, rrup_var = rupture.computeRrup(sta_lons, sta_lats, elev)
            rjb_mean, rjb_var = rupture.computeRjb(sta_lons, sta_lats, elev)
            rrup_var = np.full_like(rrup_mean, np.nan)
            rjb_var = np.full_like(rjb_mean, np.nan)
            gc2_dict = rupture.computeGC2(sta_lons, sta_lats, elev)
            gc2_rx = gc2_dict['rx']
            gc2_ry = gc2_dict['ry']
            gc2_ry0 = gc2_dict['ry0']
            gc2_U = gc2_dict['U']
            gc2_T = gc2_dict['T']

            # If we don't have a point rupture, then back azimuth needs
            # to be calculated to the closest point on the rupture
            self.sta_baz = []
            for i in range(len(self.pstreams)):
                dists = []
                bazs = []
                for quad in rupture._quadrilaterals:
                    P0, P1, P2, P3 = quad
                    for point in [P0, P1]:
                        dist, az, baz = gps2dist_azimuth(
                            point.y, point.x, sta_lats[i], sta_lons[i])
                        dists.append(dist)
                        bazs.append(baz)
                self.sta_baz.append(bazs[np.argmin(dists)])

        for i, stream in enumerate(self.pstreams):
            logging.info(
                'Calculating station metrics for %s...' % stream.get_id())
            summary = StationSummary.from_config(
                stream, event=event, config=self.gmrecords.conf,
                calc_waveform_metrics=False,
                calc_station_metrics=False,
                rupture=rupture, vs30_grids=self.vs30_grids)

            summary._distances = {
                'epicentral': self.sta_repi[i],
                'hypocentral': self.sta_rhyp[i],
                'rupture': rrup_mean[i],
                'rupture_var': rrup_var[i],
                'joyner_boore': rjb_mean[i],
                'joyner_boore_var': rjb_var[i],
                'gc2_rx': gc2_rx[i],
                'gc2_ry': gc2_ry[i],
                'gc2_ry0': gc2_ry0[i],
                'gc2_U': gc2_U[i],
                'gc2_T': gc2_T[i]
            }
            summary._back_azimuth = self.sta_baz[i]
            if self.vs30_grids is not None:
                for vs30_name in self.vs30_grids.keys():
                    tmpgrid = self.vs30_grids[vs30_name]
                    summary._vs30[vs30_name] = {
                        'value': tmpgrid['grid_object'].getValue(
                            float(sta_lats[i]), float(sta_lons[i])),
                        'column_header': tmpgrid['column_header'],
                        'readme_entry': tmpgrid['readme_entry'],
                        'units': tmpgrid['units']
                    }

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
                overwrite=self.gmrecords.args.overwrite)
            logging.info('Added station metrics to workspace files '
                         'with tag \'%s\'.' % self.gmrecords.args.label)

        self.workspace.close()
        return event.id

    def _get_ps2ff_splines(self):
        # TODO: Make these options configurable in config file.
        mscale = MagScaling.WC94
        smech = Mechanism.A
        aspect = 1.7
        mindip_deg = 10.0
        maxdip_deg = 90.0
        mindip = mindip_deg * np.pi / 180.0
        maxdip = maxdip_deg * np.pi / 180.0
        repi, Rjb_hat, Rrup_hat, Rjb_var, Rrup_var = single_event_adjustment(
            self.origin.mag, self.origin.depth, ar=aspect,
            mechanism=smech, mag_scaling=mscale,
            n_repi=13,
            min_repi=np.min(self.sta_repi) - 1e-5,
            max_repi=np.max(self.sta_repi) + 0.1,
            nxny=7, n_theta=19,
            n_dip=4, min_dip=mindip, max_dip=maxdip,
            n_eps=5, trunc=2)
        self.rjb_spline = spint.interp1d(
            repi, np.vstack((Rjb_hat, Rjb_var)),
            kind='linear', copy=False,
            assume_sorted=True)
        self.rrup_spline = spint.interp1d(
            repi, np.vstack((Rrup_hat, Rrup_var)),
            kind='linear', copy=False,
            assume_sorted=True)
