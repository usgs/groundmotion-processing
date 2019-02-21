#!/usr/bin/env python
"""
Helper functions for windowing singal and noise in a trace.
"""
from importlib import import_module
import pkg_resources
import yaml

import numpy as np

from openquake.hazardlib.gsim.base import SitesContext
from openquake.hazardlib.gsim.base import RuptureContext
from openquake.hazardlib.gsim.base import DistancesContext
from openquake.hazardlib import const
from openquake.hazardlib import imt

from obspy.geodetics.base import gps2dist_azimuth

from gmprocess.phase import PowerPicker
from gmprocess.utils import _update_params
from gmprocess.config import get_config

CONFIG = get_config()


def signal_split(
        st, event_time=None, event_lon=None, event_lat=None,
        method='velocity', vsplit=7.0):
    """
    This method tries to identifies the boundary between the noise and signal
    for the waveform. The split time is placed inside the
    'processing_parameters' key of the trace stats.

    If split_method is 'velocity', then the split between the noise and signal
    window is approximated as the arrival time of a phase with velocity equal
    to vsplit.

    If split_method is equal to 'p_arrival', then the P-wave arrival is
    used as the split between the noise and signal windows. Multiple picker
    methods are suppored and can be configured in the config file
    '~/.gmprocess/picker.conf' (TODO!).

    Args:
        st (obspy.core.stream.Stream):
            Stream of data.
        event_time (UTCDateTime):
            Event origin time.
        event_lon (float):
            Event longitude.
        event_lat (float):
            Event latitude.
        method (str):
            Method for splitting noise and signal windows. Either 'p_arrival'
            or 'velocity'.
        vsplit (float):
            Velocity (km/s) for splitting noise and signal.

    Returns:
        trace with stats dict updated to include a
        stats['processing_parameters']['signal_split'] dictionary.
    """
    for tr in st:
        if method == 'p_arrival':
            p_picks = PowerPicker(tr)
            time_to_split = p_picks[0]
        elif method == 'velocity':
            epi_dist = gps2dist_azimuth(
                lat1=event_lat,
                lon1=event_lon,
                lat2=tr.stats['coordinates']['latitude'],
                lon2=tr.stats['coordinates']['longitude'])[0]/1000.0
            time_to_split = event_time + epi_dist / vsplit
        else:
            raise ValueError('Split method must be "p_arrival" or "velocity"')

        # Update trace params
        split_params = {
            'split_time': time_to_split,
            'method': method,
            'vsplit': vsplit
        }
        tr = _update_params(tr, 'signal_split', split_params)
    return st


def signal_end(st, event_time, event_lon, event_lat, event_mag,
               method=None, vmin=None, floor=None,
               model=None, epsilon=2.0):
    """
    Estimate end of signal by using a model of the 5-95% significant
    duration, and adding this value to the "signal_split" time. This probably
    only works well when the split is estimated with a p-wave picker since
    the velocity method often ends up with split times that are well before
    signal actually starts.

    Args:
        st (obspy.core.stream.Stream):
            Stream of data.
        event_time (UTCDateTime):
            Event origin time.
        event_mag (float):
            Event magnitude.
        event_lon (float):
            Event longitude.
        event_lat (float):
            Event latitude.
        method (str):
            Method for estimating signal end time. Either 'velocity'
            or 'model'.
        vmin (float):
            Velocity (km/s) for estimating end of signal. Only used if
            method="velocity".
        floor (float):
            Minimum duration (sec) applied along with vmin.
        model (str):
            Short name of duration model to use. Must be defined in the
            gmprocess/data/modules.yml file.
        epsilon (float):
            Number of standard deviations; if epsilon is 1.0, then the signal
            window duration is the mean Ds + 1 standard deviation. Only used
            for method="model".

    Returns:
        trace with stats dict updated to include a
        stats['processing_parameters']['signal_end'] dictionary.

    """
    # Load openquake stuff if method="model"
    if method == "model":
        mod_file = pkg_resources.resource_filename(
            'gmprocess', 'data/modules.yml')
        with open(mod_file, 'r') as f:
            mods = yaml.load(f)

        # Import module
        cname, mpath = mods['modules'][model]
        dmodel = getattr(import_module(mpath), cname)()

        # Set some "conservative" inputs (in that they will tend to give
        # larger durations).
        sctx = SitesContext()
        sctx.vs30 = np.array([180.0])
        sctx.z1pt0 = np.array([0.51])
        rctx = RuptureContext()
        rctx.mag = event_mag
        rctx.rake = -90.0
        dur_imt = imt.from_string('RSD595')
        stddev_types = [const.StdDev.INTRA_EVENT]

    for tr in st:
        if method == "velocity":
            if vmin is None:
                raise ValueError('Must specify vmin if method is "velocity".')
            if floor is None:
                raise ValueError('Must specify floor if method is "velocity".')
            epi_dist = gps2dist_azimuth(
                lat1=event_lat,
                lon1=event_lon,
                lat2=tr.stats['coordinates']['latitude'],
                lon2=tr.stats['coordinates']['longitude'])[0]/1000.0
            end_time = event_time + max(floor, epi_dist / vmin)
        elif method == "model":
            if model is None:
                raise ValueError('Must specify model if method is "model".')
            epi_dist = gps2dist_azimuth(
                lat1=event_lat,
                lon1=event_lon,
                lat2=tr.stats['coordinates']['latitude'],
                lon2=tr.stats['coordinates']['longitude'])[0]/1000.0
            dctx = DistancesContext()
            # Repi >= Rrup, so substitution here should be conservative
            # (leading to larger durations).
            dctx.rrup = np.array([epi_dist])
            lnmu, lnstd = dmodel.get_mean_and_stddevs(
                sctx, rctx, dctx, dur_imt, stddev_types)
            duration = np.exp(lnmu + epsilon * lnstd[0])
            # Get split time
            split_time = \
                tr.stats['processing_parameters']['signal_split']['split_time']
            end_time = split_time + float(duration)
        else:
            raise ValueError('method must be either "velocity" or "model".')
        # Update trace params
        end_params = {
            'end_time': end_time,
            'method': method,
            'vsplit': vmin,
            'floor': floor,
            'model': model,
            'epsilon': epsilon
        }
        tr = _update_params(tr, 'signal_end', end_params)

    return st
