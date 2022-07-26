#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Helper functions for windowing singal and noise in a trace.
"""
import logging

import numpy as np
import pandas as pd

from openquake.hazardlib.gsim.base import RuptureContext
from openquake.hazardlib import const
from openquake.hazardlib import imt

from obspy.geodetics.base import gps2dist_azimuth

from gmprocess.waveform_processing.phase import (
    pick_power,
    pick_ar,
    pick_baer,
    pick_kalkan,
    pick_travel,
)
from gmprocess.utils.config import get_config
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.utils.models import load_model
from gmprocess.waveform_processing.processing_step import ProcessingStep

M_TO_KM = 1.0 / 1000


@ProcessingStep
def cut(st, sec_before_split=2.0, config=None):
    """
    Cut/trim the record.

    This method minimally requires that the windows.signal_end method has been
    run, in which case the record is trimmed to the end of the signal that
    was estimated by that method.

    To trim the beginning of the record, the sec_before_split must be
    specified, which uses the noise/signal split time that was estiamted by the
    windows.signal_split mehtod.

    # Recent changes to reflect major updates to how oq-hazardlib works:
    # https://github.com/gem/oq-engine/issues/7018

    Args:
        st (StationStream):
            Stream of data.
        sec_before_split (float):
            Seconds to trim before split. If None, then the beginning of the
            record will be unchanged.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        stream: cut streams.
    """
    if not st.passed:
        return st

    for tr in st:
        logging.debug(f"Before cut end time: {tr.stats.endtime} ")
        etime = tr.getParameter("signal_end")["end_time"]
        tr.trim(endtime=etime)
        logging.debug(f"After cut end time: {tr.stats.endtime} ")
        if sec_before_split is not None:
            split_time = tr.getParameter("signal_split")["split_time"]
            stime = split_time - sec_before_split
            logging.debug(f"Before cut start time: {tr.stats.starttime} ")
            if stime < etime:
                tr.trim(starttime=stime)
            else:
                tr.fail(
                    "The 'cut' processing step resulting in "
                    "incompatible start and end times."
                )
            logging.debug(f"After cut start time: {tr.stats.starttime} ")
        tr.setProvenance(
            "cut",
            {"new_start_time": tr.stats.starttime, "new_end_time": tr.stats.endtime},
        )
    return st


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
        if not tr.hasParameter("signal_split"):
            if st.passed:
                tr.fail("Cannot check window because no split time available.")
            continue
        # Split the noise and signal into two separate traces
        split_prov = tr.getParameter("signal_split")
        if isinstance(split_prov, list):
            split_prov = split_prov[0]
        split_time = split_prov["split_time"]
        noise_duration = split_time - tr.stats.starttime
        signal_duration = tr.stats.endtime - split_time
        if noise_duration < min_noise_duration:
            tr.fail("Failed noise window duration check.")
        if signal_duration < min_signal_duration:
            tr.fail("Failed signal window duration check.")

    return st


def signal_split(st, origin, model=None, config=None):
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
        model (TauPyModel):
            TauPyModel object for computing travel times.
        config (dict):
            Dictionary containing system configuration information.

    Returns:
        trace with stats dict updated to include a
        stats['processing_parameters']['signal_split'] dictionary.
    """
    if config is None:
        config = get_config()
    picker_config = config["pickers"]

    loc, mean_snr = pick_travel(st, origin, model)
    if loc > 0:
        tsplit = st[0].stats.starttime + loc
        preferred_picker = "travel_time"
    else:
        pick_methods = ["ar", "baer", "power", "kalkan"]
        rows = []
        for pick_method in pick_methods:
            try:
                if pick_method == "ar":
                    loc, mean_snr = pick_ar(
                        st, picker_config=picker_config, config=config
                    )
                elif pick_method == "baer":
                    loc, mean_snr = pick_baer(
                        st, picker_config=picker_config, config=config
                    )
                elif pick_method == "power":
                    loc, mean_snr = pick_power(
                        st, picker_config=picker_config, config=config
                    )
                elif pick_method == "kalkan":
                    loc, mean_snr = pick_kalkan(
                        st, picker_config=picker_config, config=config
                    )
                elif pick_method == "yeck":
                    loc, mean_snr = pick_kalkan(st)
            except BaseException:
                loc = -1
                mean_snr = np.nan
            rows.append(
                {
                    "Stream": st.get_id(),
                    "Method": pick_method,
                    "Pick_Time": loc,
                    "Mean_SNR": mean_snr,
                }
            )
        df = pd.DataFrame(rows)

        max_snr = df["Mean_SNR"].max()
        if not np.isnan(max_snr):
            maxrow = df[df["Mean_SNR"] == max_snr].iloc[0]
            tsplit = st[0].stats.starttime + maxrow["Pick_Time"]
            preferred_picker = maxrow["Method"]
        else:
            tsplit = -1

    # the user may have specified a p_arrival_shift value.
    # this is used to shift the P arrival time (i.e., the break between the
    # noise and signal windows).
    shift = 0.0
    if "p_arrival_shift" in picker_config:
        shift = picker_config["p_arrival_shift"]
        if tsplit + shift >= st[0].stats.starttime:
            tsplit += shift

    if tsplit >= st[0].stats.starttime:
        # Update trace params
        split_params = {
            "split_time": tsplit,
            "method": "p_arrival",
            "picker_type": preferred_picker,
        }
        for tr in st:
            tr.setParameter("signal_split", split_params)

    return st


def signal_end(
    st,
    event_time,
    event_lon,
    event_lat,
    event_mag,
    method="model",
    vmin=1.0,
    floor=120.0,
    model="AS16",
    epsilon=3.0,
):
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
            Method for estimating signal end time. Can be 'velocity', 'model',
            'magnitude', or 'none'.
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
        dmodel = load_model(model)

        # Set some "conservative" inputs (in that they will tend to give
        # larger durations).
        rctx = RuptureContext()
        rctx.mag = event_mag
        rctx.rake = -90.0
        rctx.vs30 = np.array([180.0])
        rctx.z1pt0 = np.array([0.51])
        dur_imt = imt.from_string("RSD595")
        stddev_types = [const.StdDev.TOTAL]

    for tr in st:
        if not tr.hasParameter("signal_split"):
            logging.warning("No signal split in trace, cannot set signal end.")
            continue
        if method == "velocity":
            if vmin is None:
                raise ValueError('Must specify vmin if method is "velocity".')
            if floor is None:
                raise ValueError('Must specify floor if method is "velocity".')
            epi_dist = (
                gps2dist_azimuth(
                    lat1=event_lat,
                    lon1=event_lon,
                    lat2=tr.stats["coordinates"]["latitude"],
                    lon2=tr.stats["coordinates"]["longitude"],
                )[0]
                / 1000.0
            )
            end_time = event_time + max(floor, epi_dist / vmin)
        elif method == "model":
            if model is None:
                raise ValueError('Must specify model if method is "model".')
            epi_dist = (
                gps2dist_azimuth(
                    lat1=event_lat,
                    lon1=event_lon,
                    lat2=tr.stats["coordinates"]["latitude"],
                    lon2=tr.stats["coordinates"]["longitude"],
                )[0]
                / 1000.0
            )
            # Repi >= Rrup, so substitution here should be conservative
            # (leading to larger durations).
            rctx.rrup = np.array([epi_dist])
            rctx.sids = np.array(range(np.size(rctx.rrup)))
            lnmu, lnstd = dmodel.get_mean_and_stddevs(
                rctx, rctx, rctx, dur_imt, stddev_types
            )
            duration = np.exp(lnmu + epsilon * lnstd[0])
            # Get split time
            split_time = tr.getParameter("signal_split")["split_time"]
            end_time = split_time + float(duration)
        elif method == "magnitude":
            # According to Hamid:
            #     duration is {mag}/2 minutes starting 30 seconds
            #     before the origin time
            duration = event_mag / 2.0 * 60.0
            end_time = event_time + duration - 30.0
        elif method == "none":
            # need defaults
            end_time = tr.stats.endtime
        else:
            raise ValueError(
                'method must be one of: "velocity", "model", "magnitude", or "none".'
            )
        # Update trace params
        end_params = {
            "end_time": end_time,
            "method": method,
            "vsplit": vmin,
            "floor": floor,
            "model": model,
            "epsilon": epsilon,
        }
        tr.setParameter("signal_end", end_params)

    return st


@ProcessingStep
def trim_multiple_events(
    st,
    origin,
    catalog,
    travel_time_df,
    pga_factor,
    pct_window_reject,
    gmpe,
    site_parameters,
    rupture_parameters,
):
    """
    Uses a catalog (list of ScalarEvents) to handle cases where a trace might
    contain signals from multiple events. The catalog should contain events
    down to a low enough magnitude in relation to the events of interest.
    Overall, the algorithm is as follows:

    1) For each earthquake in the catalog, get the P-wave travel time
       and estimated PGA at this station.

    2) Compute the PGA (of the as-recorded horizontal channels).

    3) Select the P-wave arrival times across all events for this record
       that are (a) within the signal window, and (b) the predicted PGA is
       greater than pga_factor times the PGA from step #1.

    4) If any P-wave arrival times match the above criteria, then if any of
       the arrival times fall within in the first pct_window_reject*100%
       of the signal window, then reject the record. Otherwise, trim the
       record such that the end time does not include any of the arrivals
       selected in step #3.

    Args:
        st (StationStream):
            Stream of data.
        origin (ScalarEvent):
            ScalarEvent object associated with the StationStream.
        catalog (list):
            List of ScalarEvent objects.
        travel_time_df (DataFrame):
            A pandas DataFrame that contains the travel time information
            (obtained from
             gmprocess.waveform_processing.phase.create_travel_time_dataframe).
            The columns in the DataFrame are the station ids and the indices
            are the earthquake ids.
        pga_factor (float):
            A decimal factor used to determine whether the predicted PGA
            from an event arrival is significant enough that it should be
            considered for removal.
        pct_window_reject (float):
           A decimal from 0.0 to 1.0 used to determine if an arrival should
            be trimmed from the record, or if the entire record should be
            rejected. If the arrival falls within the first
            pct_window_reject * 100% of the signal window, then the entire
            record will be rejected. Otherwise, the record will be trimmed
            appropriately.
        gmpe (str):
            Short name of the GMPE to use. Must be defined in the modules file.
        site_parameters (dict):
            Dictionary of site parameters to input to the GMPE.
        rupture_parameters:
            Dictionary of rupture parameters to input to the GMPE.

    Returns:
        StationStream: Processed stream.

    """

    if not st.passed:
        return st

    # Check that we know the signal split for each trace in the stream
    for tr in st:
        if not tr.hasParameter("signal_split"):
            return st

    signal_window_starttime = st[0].getParameter("signal_split")["split_time"]

    arrivals = travel_time_df[st[0].stats.network + "." + st[0].stats.station]
    arrivals = arrivals.sort_values()

    # Filter by any arrival times that appear in the signal window
    arrivals = arrivals[
        (arrivals > signal_window_starttime) & (arrivals < st[0].stats.endtime)
    ]

    # Make sure we remove the arrival that corresponds to the event of interest
    if origin.id in arrivals.index:
        arrivals.drop(index=origin.id, inplace=True)

    if arrivals.empty:
        return st

    # Calculate the recorded PGA for this record
    stasum = StationSummary.from_stream(st, ["ROTD(50.0)"], ["PGA"])
    recorded_pga = stasum.get_pgm("PGA", "ROTD(50.0)")

    # Load the GMPE model
    gmpe = load_model(gmpe)

    # Generic context
    rctx = RuptureContext()

    # Make sure that site parameter values are converted to numpy arrays
    site_parameters_copy = site_parameters.copy()
    for k, v in site_parameters_copy.items():
        site_parameters_copy[k] = np.array([site_parameters_copy[k]])
    rctx.__dict__.update(site_parameters_copy)

    # Filter by arrivals that have significant expected PGA using GMPE
    is_significant = []
    for eqid, arrival_time in arrivals.items():
        event = next(event for event in catalog if event.id == eqid)

        # Set rupture parameters
        rctx.__dict__.update(rupture_parameters)
        rctx.mag = event.magnitude

        # TODO: distances should be calculated when we refactor to be
        # able to import distance calculations
        rctx.repi = np.array(
            [
                gps2dist_azimuth(
                    st[0].stats.coordinates.latitude,
                    st[0].stats.coordinates.longitude,
                    event.latitude,
                    event.longitude,
                )[0]
                / 1000
            ]
        )
        rctx.rjb = rctx.repi
        rctx.rhypo = np.sqrt(rctx.repi**2 + event.depth_km**2)
        rctx.rrup = rctx.rhypo
        rctx.sids = np.array(range(np.size(rctx.rrup)))
        pga, sd = gmpe.get_mean_and_stddevs(rctx, rctx, rctx, imt.PGA(), [])

        # Convert from ln(g) to %g
        predicted_pga = 100 * np.exp(pga[0])
        if predicted_pga > (pga_factor * recorded_pga):
            is_significant.append(True)
        else:
            is_significant.append(False)

    significant_arrivals = arrivals[is_significant]
    if significant_arrivals.empty:
        return st

    # Check if any of the significant arrivals occur within the
    signal_length = st[0].stats.endtime - signal_window_starttime
    cutoff_time = signal_window_starttime + pct_window_reject * (signal_length)
    if (significant_arrivals < cutoff_time).any():
        for tr in st:
            tr.fail(
                "A significant arrival from another event occurs within "
                "the first %s percent of the signal window" % (100 * pct_window_reject)
            )

    # Otherwise, trim the stream at the first significant arrival
    else:
        for tr in st:
            signal_end = tr.getParameter("signal_end")
            signal_end["end_time"] = significant_arrivals[0]
            signal_end["method"] = "Trimming before right another event"
            tr.setParameter("signal_end", signal_end)
        cut(st)

    return st
