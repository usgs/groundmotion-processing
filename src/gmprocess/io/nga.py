#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Helper functions for working with the NGA flatfile.
"""

# stdlib imports
import os
import logging

# third party imports
import numpy as np
import pandas as pd
from obspy.geodetics.base import gps2dist_azimuth

from gmprocess.utils.constants import DATA_DIR


def get_nga_record_sequence_no(st, eq_name, distance_tolerance=50):
    """
    Returns the associate NGA record sequence number for a given StationStream.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Station stream to get record sequence number for.
        eq_name (str):
            Earthquake name for finding NGA record sequence numbers. Must
            match a value in the 'Earthquake Name' column of the file
            gmprocess/data/nga_w2_selected.csv.
        distance_tolerance (float):
            Distance tolerance (in meters) between StationStream location
            coordinates and the NGA location coordinates.
            Default is 50 meters.

    Returns:
        int: Matching record sequence number from NGA flatfile. Returns
        numpy.nan if record sequence number is not found.

    """
    data_file = DATA_DIR / "nga_w2_selected.csv"
    df_nga = pd.read_csv(data_file)

    nga_event = df_nga.loc[df_nga["Earthquake Name"] == eq_name]

    lat = st[0].stats.coordinates.latitude
    lon = st[0].stats.coordinates.longitude

    matched_records_nos = []
    for record_idx, record in nga_event.iterrows():
        dist = gps2dist_azimuth(
            lat, lon, record["Station Latitude"], record["Station Longitude"]
        )[0]
        if dist < distance_tolerance:
            matched_records_nos.append(record["Record Sequence Number"])

    if len(matched_records_nos) > 1:
        logging.warning("Found multiple matching records.")
        return np.nan
    elif len(matched_records_nos) < 1:
        logging.warning("Did not find any matching records.")
        return np.nan
    else:
        return matched_records_nos[0]
