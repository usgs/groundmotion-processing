#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

from gmprocess.subcommands.lazy_loader import LazyLoader

np = LazyLoader("np", globals(), "numpy")
spint = LazyLoader("spint", globals(), "scipy.interpolate")
ob = LazyLoader("ob", globals(), "obspy.geodetics.base")
oqgeo = LazyLoader("oqgeo", globals(), "openquake.hazardlib.geo.geodetic")
rupt = LazyLoader("rupt", globals(), "esi_utils_rupture")
ps2ff = LazyLoader("ps2ff", globals(), "ps2ff")

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
utils = LazyLoader("utils", globals(), "gmprocess.utils")
rupt_utils = LazyLoader("rupt_utils", globals(), "gmprocess.utils.rupture_utils")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
station_summary = LazyLoader(
    "station_summary", globals(), "gmprocess.metrics.station_summary"
)
confmod = LazyLoader("confmod", globals(), "gmprocess.utils.config")

M_PER_KM = 1000


class ComputeStationMetricsModule(base.SubcommandModule):
    """Compute station metrics."""

    command_name = "compute_station_metrics"
    aliases = ("sm",)

    arguments = [
        arg_dicts.ARG_DICTS["eventid"],
        arg_dicts.ARG_DICTS["textfile"],
        arg_dicts.ARG_DICTS["label"],
        arg_dicts.ARG_DICTS["overwrite"],
    ]

    def main(self, gmrecords):
        """Compute station metrics.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        for event in self.events:
            self._event_station_metrics(event)

        self._summarize_files_created()

    def _event_station_metrics(self, event):
        self.eventid = event.id
        logging.info(f"Computing station metrics for event {self.eventid}...")
        event_dir = os.path.join(self.gmrecords.data_path, self.eventid)
        workname = os.path.normpath(
            os.path.join(event_dir, utils.constants.WORKSPACE_NAME)
        )
        if not os.path.isfile(workname):
            logging.info(
                "No workspace file found for event %s. Please run "
                "subcommand 'assemble' to generate workspace file." % self.eventid
            )
            logging.info("Continuing to next event.")
            return event.id

        self.workspace = ws.StreamWorkspace.open(workname)
        ds = self.workspace.dataset
        self._get_labels()

        config = self._get_config()

        station_list = ds.waveforms.list()
        if not len(station_list):
            self.workspace.close()
            return event.id

        rupture_file = rupt_utils.get_rupture_file(event_dir)
        origin = rupt.origin.Origin(
            {
                "id": self.eventid,
                "netid": "",
                "network": "",
                "lat": event.latitude,
                "lon": event.longitude,
                "depth": event.depth_km,
                "locstring": "",
                "mag": event.magnitude,
                "time": event.time,
            }
        )
        self.origin = origin
        rupture = rupt.factory.get_rupture(origin, rupture_file)

        self._get_labels()

        for station_id in station_list:
            streams = self.workspace.getStreams(
                event.id,
                stations=[station_id],
                labels=[self.gmrecords.args.label],
                config=config,
            )
            if not len(streams):
                raise ValueError("No matching streams found.")

            for st in streams:
                geo_tuple = ob.gps2dist_azimuth(
                    st[0].stats.coordinates.latitude,
                    st[0].stats.coordinates.longitude,
                    origin.lat,
                    origin.lon,
                )
                sta_repi = geo_tuple[0] / M_PER_KM
                sta_baz = geo_tuple[1]
                sta_rhyp = oqgeo.distance(
                    st[0].stats.coordinates.longitude,
                    st[0].stats.coordinates.latitude,
                    -st[0].stats.coordinates.elevation / M_PER_KM,
                    origin.lon,
                    origin.lat,
                    origin.depth,
                )

                if isinstance(rupture, rupt.point_rupture.PointRupture):
                    self._get_ps2ff_splines()
                    rjb_hat = self.rjb_spline(sta_repi)
                    rjb_mean = rjb_hat[0]
                    rjb_var = rjb_hat[1]
                    rrup_hat = self.rrup_spline(sta_repi)
                    rrup_mean = rrup_hat[0]
                    rrup_var = rrup_hat[1]
                    gc2_rx = np.full_like(rjb_mean, np.nan)
                    gc2_ry = np.full_like(rjb_mean, np.nan)
                    gc2_ry0 = np.full_like(rjb_mean, np.nan)
                    gc2_U = np.full_like(rjb_mean, np.nan)
                    gc2_T = np.full_like(rjb_mean, np.nan)
                else:
                    rrup_mean, rrup_var = rupture.computeRrup(
                        np.array([st[0].stats.coordinates.longitude]),
                        np.array([st[0].stats.coordinates.latitude]),
                        utils.constants.ELEVATION_FOR_DISTANCE_CALCS,
                    )
                    rjb_mean, rjb_var = rupture.computeRjb(
                        np.array([st[0].stats.coordinates.longitude]),
                        np.array([st[0].stats.coordinates.latitude]),
                        utils.constants.ELEVATION_FOR_DISTANCE_CALCS,
                    )
                    rrup_var = np.full_like(rrup_mean, np.nan)
                    rjb_var = np.full_like(rjb_mean, np.nan)
                    gc2_dict = rupture.computeGC2(
                        np.array([st[0].stats.coordinates.longitude]),
                        np.array([st[0].stats.coordinates.latitude]),
                        utils.constants.ELEVATION_FOR_DISTANCE_CALCS,
                    )
                    gc2_rx = gc2_dict["rx"]
                    gc2_ry = gc2_dict["ry"]
                    gc2_ry0 = gc2_dict["ry0"]
                    gc2_U = gc2_dict["U"]
                    gc2_T = gc2_dict["T"]

                    # If we don't have a point rupture, then back azimuth needs
                    # to be calculated to the closest point on the rupture
                    dists = []
                    bazs = []
                    for quad in rupture._quadrilaterals:
                        P0, P1, P2, P3 = quad
                        for point in [P0, P1]:
                            dist, az, baz = ob.gps2dist_azimuth(
                                point.y,
                                point.x,
                                st[0].stats.coordinates.latitude,
                                st[0].stats.coordinates.longitude,
                            )
                            dists.append(dist)
                            bazs.append(baz)
                        sta_baz = bazs[np.argmin(dists)]

                streamid = st.get_id()
                logging.info(f"Calculating station metrics for {streamid}...")
                summary = station_summary.StationSummary.from_config(
                    st,
                    event=event,
                    config=config,
                    calc_waveform_metrics=False,
                    calc_station_metrics=False,
                    rupture=rupture,
                )

                summary._distances = {
                    "epicentral": sta_repi,
                    "hypocentral": sta_rhyp,
                    "rupture": rrup_mean,
                    "rupture_var": rrup_var,
                    "joyner_boore": rjb_mean,
                    "joyner_boore_var": rjb_var,
                    "gc2_rx": gc2_rx,
                    "gc2_ry": gc2_ry,
                    "gc2_ry0": gc2_ry0,
                    "gc2_U": gc2_U,
                    "gc2_T": gc2_T,
                }
                summary._back_azimuth = sta_baz

                xmlstr = summary.get_station_xml()
                if config["read"]["use_streamcollection"]:
                    chancode = st.get_inst()
                else:
                    chancode = st[0].stats.channel
                metricpath = "/".join(
                    [
                        ws.format_netsta(st[0].stats),
                        ws.format_nslit(st[0].stats, chancode, self.eventid),
                    ]
                )
                self.workspace.insert_aux(
                    xmlstr,
                    "StationMetrics",
                    metricpath,
                    overwrite=self.gmrecords.args.overwrite,
                )
                logging.info(
                    "Added station metrics to workspace files "
                    "with tag '%s'." % self.gmrecords.args.label
                )

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
        repi, Rjb_hat, Rrup_hat, Rjb_var, Rrup_var = ps2ff.run.single_event_adjustment(
            self.origin.mag,
            self.origin.depth,
            ar=aspect,
            mechanism=smech,
            mag_scaling=mscale,
            n_repi=30,
            min_repi=0.1,
            max_repi=2000,
            nxny=7,
            n_theta=19,
            n_dip=4,
            min_dip=mindip,
            max_dip=maxdip,
            n_eps=5,
            trunc=2,
        )
        self.rjb_spline = spint.interp1d(
            repi,
            np.vstack((Rjb_hat, Rjb_var)),
            kind="linear",
            copy=False,
            assume_sorted=True,
        )
        self.rrup_spline = spint.interp1d(
            repi,
            np.vstack((Rrup_hat, Rrup_var)),
            kind="linear",
            copy=False,
            assume_sorted=True,
        )
