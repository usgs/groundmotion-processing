#!/usr/bin/env python
"""
Helper functions for windowing singal and noise in a trace.
"""
import os
from importlib import import_module
import pkg_resources
import yaml
import logging

import numpy as np

from openquake.hazardlib.gsim.base import SitesContext
from openquake.hazardlib.gsim.base import RuptureContext
from openquake.hazardlib.gsim.base import DistancesContext
from openquake.hazardlib import const
from openquake.hazardlib import imt

from obspy.geodetics.base import gps2dist_azimuth
from obspy.signal.trigger import ar_pick, pk_baer

from gmprocess.phase import PowerPicker
from gmprocess.config import get_config

M_TO_KM = 1.0 / 1000


def window_checks(st, min_noise_duration=0.5, min_signal_duration=5.0):
    """
    Check if the split/end windowing have long enough durations.

    Args:
        st (StationStream):
            Stream of data.
        min_noise_duration (float):
            Minimum duration of noise window (sec).
        min_signal_duration (float):
            Minimum duration of signal window (sec).


    """
    for tr in st:
        # Split the noise and signal into two separate traces
        split_prov = tr.getParameter('signal_split')
        if isinstance(split_prov, list):
            split_prov = split_prov[0]
        split_time = split_prov['split_time']
        noise = tr.copy().trim(endtime=split_time)
        signal = tr.copy().trim(starttime=split_time)
        noise_duration = noise.stats.endtime - noise.stats.starttime
        signal_duration = signal.stats.endtime - signal.stats.starttime
        if noise_duration < min_noise_duration:
            tr.fail('Failed noise window duraiton check.')
        if signal_duration < min_signal_duration:
            tr.fail('Failed signal window duraiton check.')

    return st


def signal_split(
        st, event_time=None, event_lon=None, event_lat=None,
        method='velocity', vsplit=7.0, picker_config=None):
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
    '~/.gmprocess/picker.yml

    Args:
        st (StationStream):
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
    if picker_config is None:
        picker_config = get_config(picker=True)

    if method == 'p_arrival':
        preferred_picker = picker_config['order_of_preference'][0]

        if preferred_picker == 'ar':
            # Get the east, north, and vertical components from the stream
            st_e = st.select(channel='??[E1]')
            st_n = st.select(channel='??[N2]')
            st_z = st.select(channel='??[Z3]')

            # Check if we found one of each component
            # If not, use the next picker in the order of preference
            if len(st_e) != 1 or len(st_n) != 1 or len(st_z) != 1:
                logging.warning('Unable to perform AR picker.')
                logging.warning('Using next available phase picker.')
                preferred_picker = picker_config['order_of_preference'][1]
            else:
                tdiff = ar_pick(st_z[0].data, st_n[0].data, st_e[0].data,
                                st_z[0].stats.sampling_rate,
                                **picker_config['ar'])[0]
                tsplit = st[0].stats.starttime + tdiff

        if preferred_picker in ['baer', 'cwb']:
            tdiffs = []
            for tr in st:
                if preferred_picker == 'baer':
                    pick_sample = pk_baer(tr.data, tr.stats.sampling_rate,
                                          **picker_config['baer'])[0]
                    tr_tdiff = pick_sample * tr.stats.delta
                else:
                    tr_tdiff = PowerPicker(tr)[0] - tr.stats.starttime
                tdiffs.append(tr_tdiff)
            tdiff = min(tdiffs)
            tsplit = st[0].stats.starttime + tdiff

        if preferred_picker not in ['ar', 'baer', 'cwb']:
            raise ValueError('Not a valid picker.')

    elif method == 'velocity':
        epi_dist = gps2dist_azimuth(
            lat1=event_lat,
            lon1=event_lon,
            lat2=st[0].stats['coordinates']['latitude'],
            lon2=st[0].stats['coordinates']['longitude'])[0] * M_TO_KM
        tsplit = event_time + epi_dist / vsplit
        preferred_picker = None
    else:
        raise ValueError('Split method must be "p_arrival" or "velocity"')

    if tsplit >= st[0].times('utcdatetime')[0]:
        # Update trace params
        split_params = {
            'split_time': tsplit,
            'method': method,
            'vsplit': vsplit,
            'picker_type': preferred_picker
        }
        for tr in st:
            tr.setParameter('signal_split', split_params)

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
        st (StationStream):
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
            'gmprocess', os.path.join('data', 'modules.yml'))
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
        if not tr.hasParameter('signal_split'):
            continue
        if method == "velocity":
            if vmin is None:
                raise ValueError('Must specify vmin if method is "velocity".')
            if floor is None:
                raise ValueError('Must specify floor if method is "velocity".')
            epi_dist = gps2dist_azimuth(
                lat1=event_lat,
                lon1=event_lon,
                lat2=tr.stats['coordinates']['latitude'],
                lon2=tr.stats['coordinates']['longitude'])[0] / 1000.0
            end_time = event_time + max(floor, epi_dist / vmin)
        elif method == "model":
            if model is None:
                raise ValueError('Must specify model if method is "model".')
            epi_dist = gps2dist_azimuth(
                lat1=event_lat,
                lon1=event_lon,
                lat2=tr.stats['coordinates']['latitude'],
                lon2=tr.stats['coordinates']['longitude'])[0] / 1000.0
            dctx = DistancesContext()
            # Repi >= Rrup, so substitution here should be conservative
            # (leading to larger durations).
            dctx.rrup = np.array([epi_dist])
            lnmu, lnstd = dmodel.get_mean_and_stddevs(
                sctx, rctx, dctx, dur_imt, stddev_types)
            duration = np.exp(lnmu + epsilon * lnstd[0])
            # Get split time
            split_time = tr.getParameter('signal_split')['split_time']
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
        tr.setParameter('signal_end', end_params)

    return st
