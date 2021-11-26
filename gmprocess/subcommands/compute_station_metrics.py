#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

from gmprocess.subcommands.lazy_loader import LazyLoader
np = LazyLoader('np', globals(), 'numpy')
spint = LazyLoader('spint', globals(), 'scipy.interpolate')
gmt = LazyLoader('gmt', globals(), 'mapio.gmt')
ob = LazyLoader('ob', globals(), 'obspy.geodetics.base')
oqgeo = LazyLoader('oqgeo', globals(), 'openquake.hazardlib.geo.geodetic')
rupt = LazyLoader('rupt', globals(), 'impactutils.rupture')
ps2ff = LazyLoader('ps2ff', globals(), 'ps2ff')

arg_dicts = LazyLoader(
    'arg_dicts', globals(), 'gmprocess.subcommands.arg_dicts')
base = LazyLoader('base', globals(), 'gmprocess.subcommands.base')
utils = LazyLoader('utils', globals(), 'gmprocess.utils')
rupt_utils = LazyLoader(
    'rupt_utils', globals(), 'gmprocess.utils.rupture_utils')
ws = LazyLoader('ws', globals(), 'gmprocess.io.asdf.stream_workspace')
station_summary = LazyLoader(
    'station_summary', globals(), 'gmprocess.metrics.station_summary')

M_PER_KM = 1000


class ComputeStationMetricsModule(base.SubcommandModule):
    """Compute station metrics.
    """
    command_name = 'compute_station_metrics'
    aliases = ('sm', )

    arguments = [
        arg_dicts.ARG_DICTS['eventid'],
        arg_dicts.ARG_DICTS['textfile'],
        arg_dicts.ARG_DICTS['label'],
        arg_dicts.ARG_DICTS['overwrite']
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
                    vs30_grids[vs30_name]['grid_object'] = gmt.GMTGrid.load(
                        vs30_grids[vs30_name]['file'])
        self.vs30_grids = vs30_grids

        for event in self.events:
            self._event_station_metrics(event)

        self._summarize_files_created()

    def _event_station_metrics(self, event):
        self.eventid = event.id
        logging.info('Computing station metrics for event %s...'
                     % self.eventid)
        event_dir = os.path.join(self.gmrecords.data_path, self.eventid)
        workname = os.path.normpath(
            os.path.join(event_dir, utils.constants.WORKSPACE_NAME))
        if not os.path.isfile(workname):
            logging.info(
                'No workspace file found for event %s. Please run '
                'subcommand \'assemble\' to generate workspace file.'
                % self.eventid)
            logging.info('Continuing to next event.')
            return event.id

        self.workspace = ws.StreamWorkspace.open(workname)
        ds = self.workspace.dataset
        self._get_labels()

        rupture_file = rupt_utils.get_rupture_file(event_dir)
        origin = rupt.origin.Origin({
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
        rupture = rupt.factory.get_rupture(origin, rupture_file)

        sta_lats = []
        sta_lons = []
        sta_elev = []
        self.sta_repi = []
        self.sta_rhyp = []
        self.sta_baz = []

        station_list = ds.waveforms.list()
        self._get_labels()

        for station_id in station_list:
            streams = self.workspace.getStreams(
                event.id,
                stations=[station_id],
                labels=[self.gmrecords.args.label],
                config=self.gmrecords.conf
            )
            if not len(streams):
                raise ValueError('No matching streams found.')

            for st in streams:
                sta_lats.append(st[0].stats.coordinates.latitude)
                sta_lons.append(st[0].stats.coordinates.longitude)
                sta_elev.append(st[0].stats.coordinates.elevation)
                geo_tuple = ob.gps2dist_azimuth(
                    st[0].stats.coordinates.latitude,
                    st[0].stats.coordinates.longitude,
                    origin.lat, origin.lon)
                self.sta_repi.append(geo_tuple[0] / M_PER_KM)
                self.sta_baz.append(geo_tuple[1])
                self.sta_rhyp.append(
                    oqgeo.distance(
                        st[0].stats.coordinates.longitude,
                        st[0].stats.coordinates.latitude,
                        -st[0].stats.coordinates.elevation / M_PER_KM,
                        origin.lon, origin.lat, origin.depth)
                )

        if isinstance(rupture, rupt.point_rupture.PointRupture):
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
            sta_lons = np.array(sta_lons)
            sta_lats = np.array(sta_lats)
            elev = np.full_like(
                sta_lons, utils.constants.ELEVATION_FOR_DISTANCE_CALCS)
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
            for i in range(len(station_list)):
                dists = []
                bazs = []
                for quad in rupture._quadrilaterals:
                    P0, P1, P2, P3 = quad
                    for point in [P0, P1]:
                        dist, az, baz = ob.gps2dist_azimuth(
                            point.y, point.x, sta_lats[i], sta_lons[i])
                        dists.append(dist)
                        bazs.append(baz)
                self.sta_baz.append(bazs[np.argmin(dists)])

        # for station_id in station_list:
        for i, station_id in enumerate(station_list):
            streams = self.workspace.getStreams(
                event.id,
                stations=[station_id],
                labels=[self.gmrecords.args.label],
                config=self.gmrecords.conf
            )
            if not len(streams):
                raise ValueError('No matching streams found.')

            for stream in streams:
                logging.info(
                    'Calculating station metrics for %s...' % stream.get_id())
                summary = station_summary.StationSummary.from_config(
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
                    ws.format_netsta(stream[0].stats),
                    ws.format_nslit(
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
        mscale = ps2ff.constants.MagScaling.WC94
        smech = ps2ff.constants.Mechanism.A
        aspect = 1.7
        mindip_deg = 10.0
        maxdip_deg = 90.0
        mindip = mindip_deg * np.pi / 180.0
        maxdip = maxdip_deg * np.pi / 180.0
        repi, Rjb_hat, Rrup_hat, Rjb_var, Rrup_var = \
            ps2ff.run.single_event_adjustment(
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
