#!/usr/bin/env python
"""
Helper functions for windowing singal and noise in a trace.
"""
import os
from importlib import import_module
import pkg_resources
import yaml

import numpy as np
import pandas as pd

from openquake.hazardlib.gsim.base import SitesContext
from openquake.hazardlib.gsim.base import RuptureContext
from openquake.hazardlib.gsim.base import DistancesContext
from openquake.hazardlib import const
from openquake.hazardlib import imt

from obspy.geodetics.base import gps2dist_azimuth

from gmprocess.phase import (
    pick_power, pick_ar, pick_baer, pick_kalkan, pick_travel)
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
        if not tr.hasParameter('signal_split'):
            if st.passed:
                tr.fail('Cannot check window because no split time available.')
            continue
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
            tr.fail('Failed noise window duration check.')
        if signal_duration < min_signal_duration:
            tr.fail('Failed signal window duration check.')

    return st


def signal_split(
        st, origin,
        picker_config=None,
        config=None):
    """
    This method tries to identifies the boundary between the noise and signal
    for the waveform. The split time is placed inside the
    'processing_parameters' key of the trace stats.

    The P-wave arrival is used as the split between the noise and signal
    windows. Multiple picker methods are suppored and can be configured in the
    config file
    '~/.gmprocess/picker.yml

    Args:
        st (StationStream):
            Stream of data.
        origin (ScalarEvent):
            ScalarEvent object.
        picker_config (dict):
            Dictionary containing picker configuration information.
        config (dict):
            Dictionary containing system configuration information.

    Returns:
        trace with stats dict updated to include a
        stats['processing_parameters']['signal_split'] dictionary.
    """
    if picker_config is None:
        picker_config = get_config(section='pickers')
    if config is None:
        config = get_config()

    loc, mean_snr = pick_travel(st, origin,
                                picker_config=picker_config)
    if loc > 0:
        tsplit = st[0].stats.starttime + loc
        preferred_picker = 'travel_time'
    else:
        pick_methods = ['ar', 'baer', 'power', 'kalkan']
        columns = ['Stream', 'Method', 'Pick_Time', 'Mean_SNR']
        df = pd.DataFrame(columns=columns)
        for pick_method in pick_methods:
            try:
                if pick_method == 'ar':
                    loc, mean_snr = pick_ar(
                        st, picker_config=picker_config, config=config)
                elif pick_method == 'baer':
                    loc, mean_snr = pick_baer(
                        st, picker_config=picker_config, config=config)
                elif pick_method == 'power':
                    loc, mean_snr = pick_power(
                        st, picker_config=picker_config, config=config)
                elif pick_method == 'kalkan':
                    loc, mean_snr = pick_kalkan(st,
                                                picker_config=picker_config,
                                                config=config)
                elif pick_method == 'yeck':
                    loc, mean_snr = pick_kalkan(st)
            except Exception:
                loc = -1
                mean_snr = np.nan
            row = {'Stream': st.get_id(),
                   'Method': pick_method,
                   'Pick_Time': loc,
                   'Mean_SNR': mean_snr}
            df = df.append(row, ignore_index=True)

        max_snr = df['Mean_SNR'].max()
        if not np.isnan(max_snr):
            maxrow = df[df['Mean_SNR'] == max_snr].iloc[0]
            tsplit = st[0].stats.starttime + maxrow['Pick_Time']
            preferred_picker = maxrow['Method']
        else:
            tsplit = -1

    if tsplit >= st[0].stats.starttime:
        # Update trace params
        split_params = {
            'split_time': tsplit,
            'method': 'p_arrival',
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
