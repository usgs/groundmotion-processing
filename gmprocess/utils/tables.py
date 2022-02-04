#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that provides functions for manipulating the various tables
(pandas DataFrames) produced by gmprocess.
"""

import re
import numpy as np

from gmprocess.utils.constants import TABLE_FLOAT_STRING_FORMAT


def set_precisions(df):
    """
    Sets the string format for float point number columns in the DataFrame.

    Args:
        df (pandas.DataFrame):
            Table for setting precision.

    Returns:
        pandas.DataFrame: The modified table.
    """

    # Create a copy so we're not modifying the original DF
    df = df.copy()
    for regex, str_format in TABLE_FLOAT_STRING_FORMAT.items():
        r = re.compile(regex, re.IGNORECASE)
        columns = list(filter(r.match, df.columns))
        for col in columns:
            df[col] = df[col].map(lambda x: str_format % x)
    return df


def _get_table_row(stream, summary, event, imc):
    if imc.lower() == "channels":
        if len(stream) > 1:
            raise ValueError("Stream must be length 1 to get row for imc=='channels'.")
        chan = stream[0]
        chan_lowfilt = chan.getProvenance("lowpass_filter")
        chan_highfilt = chan.getProvenance("highpass_filter")
        chan_lowpass = np.nan
        chan_highpass = np.nan
        if len(chan_lowfilt):
            chan_lowpass = chan_lowfilt[0]["corner_frequency"]
        if len(chan_highfilt):
            chan_highpass = chan_highfilt[0]["corner_frequency"]
        filter_dict = {"Lowpass": chan_lowpass, "Highpass": chan_highpass}
    elif imc == "Z":
        z = stream.select(channel="*Z")
        if not len(z):
            return {}
        z = z[0]
        z_lowfilt = z.getProvenance("lowpass_filter")
        z_highfilt = z.getProvenance("highpass_filter")
        z_lowpass = np.nan
        z_highpass = np.nan
        if len(z_lowfilt):
            z_lowpass = z_lowfilt[0]["corner_frequency"]
        if len(z_highfilt):
            z_highpass = z_highfilt[0]["corner_frequency"]
        filter_dict = {"ZLowpass": z_lowpass, "ZHighpass": z_highpass}
    else:
        h1 = stream.select(channel="*1")
        h2 = stream.select(channel="*2")
        if not len(h1):
            h1 = stream.select(channel="*N")
            h2 = stream.select(channel="*E")

        if not len(h1) or not len(h2):
            return {}
        h1 = h1[0]
        h2 = h2[0]

        h1_lowfilt = h1.getProvenance("lowpass_filter")
        h1_highfilt = h1.getProvenance("highpass_filter")
        h1_lowpass = np.nan
        h1_highpass = np.nan
        if len(h1_lowfilt):
            h1_lowpass = h1_lowfilt[0]["corner_frequency"]
        if len(h1_highfilt):
            h1_highpass = h1_highfilt[0]["corner_frequency"]

        h2_lowfilt = h2.getProvenance("lowpass_filter")
        h2_highfilt = h2.getProvenance("highpass_filter")
        h2_lowpass = np.nan
        h2_highpass = np.nan
        if len(h2_lowfilt):
            h2_lowpass = h2_lowfilt[0]["corner_frequency"]
        if len(h2_highfilt):
            h2_highpass = h2_highfilt[0]["corner_frequency"]
        filter_dict = {
            "H1Lowpass": h1_lowpass,
            "H1Highpass": h1_highpass,
            "H2Lowpass": h2_lowpass,
            "H2Highpass": h2_highpass,
        }

    dists = summary.distances

    row = {
        "EarthquakeId": event.id.replace("smi:local/", ""),
        "EarthquakeTime": event.time,
        "EarthquakeLatitude": event.latitude,
        "EarthquakeLongitude": event.longitude,
        "EarthquakeDepth": event.depth_km,
        "EarthquakeMagnitude": event.magnitude,
        "EarthquakeMagnitudeType": event.magnitude_type,
        "Network": stream[0].stats.network,
        "DataProvider": stream[0].stats.standard.source,
        "StationCode": stream[0].stats.station,
        "StationID": stream.get_id(),
        "StationDescription": stream[0].stats.standard.station_name,
        "StationLatitude": stream[0].stats.coordinates.latitude,
        "StationLongitude": stream[0].stats.coordinates.longitude,
        "StationElevation": stream[0].stats.coordinates.elevation,
        "SamplingRate": stream[0].stats.sampling_rate,
        "BackAzimuth": summary._back_azimuth,
        "EpicentralDistance": dists["epicentral"],
        "HypocentralDistance": dists["hypocentral"],
        "SourceFile": stream[0].stats.standard.source_file,
    }
    if "rupture" in dists:
        row.update({"RuptureDistance": dists["rupture"]})
        row.update({"RuptureDistanceVar": dists["rupture_var"]})
    if "joyner_boore" in dists:
        row.update({"JoynerBooreDistance": dists["joyner_boore"]})
        row.update({"JoynerBooreDistanceVar": dists["joyner_boore_var"]})
    if "gc2_rx" in dists:
        row.update({"GC2_rx": dists["gc2_rx"]})
    if "gc2_ry" in dists:
        row.update({"GC2_ry": dists["gc2_ry"]})
    if "gc2_ry0" in dists:
        row.update({"GC2_ry0": dists["gc2_ry0"]})
    if "gc2_U" in dists:
        row.update({"GC2_U": dists["gc2_U"]})
    if "gc2_T" in dists:
        row.update({"GC2_T": dists["gc2_T"]})

    # Add the filter frequency information to the row
    row.update(filter_dict)

    # Add the Vs30 values to the row
    for vs30_dict in summary._vs30.values():
        row[vs30_dict["column_header"]] = vs30_dict["value"]

    imt_frame = summary.pgms.xs(imc, level=1)
    row.update(imt_frame.Result.to_dict())
    return row


def find_float(imt):
    """Find the float in an IMT string.

    Args:
        imt (str):
            An IMT string with a float in it (e.g., period for SA).

    Returns:
        float: the IMT float, if found, otherwise None.
    """
    try:
        return float(re.search(r"[0-9]*\.[0-9]*", imt).group())
    except AttributeError:
        return None
