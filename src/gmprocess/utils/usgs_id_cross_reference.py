#!/usr/bin/env python
import datetime
import logging
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from gmprocess.utils.logging import setup_logger

setup_logger(args=None, level="info")

DELTA_MAG = 0.5
# Can change if target event only has month, day, and year
DELTA_HOUR = 12
DIST_SCALER = 20
COORD_KM_SCALER = 0.009
ERROR_THRESH = 1.0

SEARCH_TEMPLATE = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"


class Event(object):
    def __init__(self, eventid, event_time, lat, lon, mag):
        self.eventid = eventid
        self.time = event_time
        self.latitude = lat
        self.longitude = lon
        self.depth = depth
        self.magnitude = mag


def cross_reference_to_usgs_id(project_name, eqids, mags, times, lats, lons):
    """
    Look for potential event matches for events in data and return
    a dictionary mapping the event IDs to the repsective match with the
    lowest error.
    Args:
        project_name (string):
            Project or data source name.
        eqids (np.array):
            Earthquake IDs of target events to be cross-referenced
        mags (np.array):
            Magnitudes of target events to be cross-referenced.
        times (np.array):
            Times of target events to be cross-referenced.
        lats (np.array):
            Latitudes of target events to be cross-referenced.
        lons (np.array):
            Longitudes of target events to be cross-referenced.
    """
    event_matches = match_to_usgs_id(eqids, mags, times, lats, lons)
    mag_range = get_magnitude_range(mags)
    mag_rates = parse_by_magnitude(eqids, mags, mag_range, event_matches)
    plot_match_rate_by_mag(project_name, mag_range, mag_rates)
    write_summary(project_name, event_matches)


def match_to_usgs_id(eqids, mags, times, lats, lons):
    """
    Look for potential event matches for events in data and return a
    dictionary mapping the event IDs to the repsective match with
    the lowest error.
    Args:
        eqids (np.array):
            Earthquake IDs of target events to be cross-referenced
        mags (np.array):
            Magnitudes of target events to be cross-referenced.
        times (np.array):
            Times of target events to be cross-referenced.
        lats (np.array):
            Latitudes of target events to be cross-referenced.
        lons (np.array):
            Longitudes of target events to be cross-referenced.
    Returns:
        event_matches (dictionary): Map of target event IDs to dictionary
        of matching USGS ID and event attributes.
    """
    # Converting datetime object
    times = [
        datetime.datetime.utcfromtimestamp(time.astype("O") / 1e9)
        for time in times
        if isinstance(time, np.datetime64)
    ]

    event_matches = {}
    warning_ids = []
    for idx, eqid in enumerate(eqids):
        # Set target atrribute dictionary
        target = set_target(mags[idx], times[idx], lats[idx], lons[idx])
        # Initial search buffers
        buffer = set_buffer(target)

        match_dict = {
            "magnitude": target["mag"],
            "time": target["time"],
            "latitude": target["lat"],
            "longitude": target["lon"],
            "usgs_id": None,
            "usgs_magnitude": None,
            "usgs_time": None,
            "usgs_latitude": None,
            "usgs_longitude": None,
            "error": None,
        }

        # Libcomcat search for matching events
        try:
            usgs_events = find_events(target, buffer)
            num_events_found = len(usgs_events)
            logging.info(
                "EQID %s: %d potential match(es) found" % (eqid, num_events_found)
            )

            if num_events_found == 1:
                usgs_event = usgs_events[0]
                min_error = calculate_error(usgs_event, buffer, target)
            elif num_events_found > 1:
                matching_event = usgs_events[0]
                min_error = 100
                for event in usgs_events:
                    total_error = calculate_error(event, buffer, target)
                    is_unique = all(
                        [
                            True if v["usgs_id"] != event.id else False
                            for v in event_matches.values()
                        ]
                    )
                    if total_error < min_error and is_unique:
                        matching_event = event
                        min_error = total_error
                usgs_event = matching_event
            else:
                logging.warning("NO MATCH FOUND")
                event_matches[eqid] = match_dict
                continue
            logging.info(f"Match Error: {min_error:.4f}")
            if min_error >= ERROR_THRESH:
                logging.warning("HIGH ERROR")
                warning_ids.append(eqid)

            match_dict["error"] = min_error
            match_dict["usgs_id"] = usgs_event.id
            match_dict["usgs_magnitude"] = usgs_event.magnitude
            match_dict["usgs_time"] = usgs_event.time
            match_dict["usgs_latitude"] = usgs_event.latitude
            match_dict["usgs_longitude"] = usgs_event.longitude

            event_matches[eqid] = match_dict
        except Exception:
            # In case of libcomcat connectivity issue
            event_matches[eqid] = match_dict

    match_rate = match_percentage(eqids, event_matches)
    logging.info(f"Event Matching Success: {match_rate * 100:.2f} %")
    return event_matches


def get_magnitude_range(magnitudes):
    """
    Determine magnitude span of events trying to be matched.
    Args:
        magnitudes (array):
           Array of event magnitudes.
    Returns:
        mag_range (list): Integer range of event magnitudes.
    """
    max_m = max(magnitudes)
    max_l = min(magnitudes)
    mag_range = list(range(int(max_l), int(max_m) + 1))
    return mag_range


def parse_by_magnitude(eqids, magnitudes, mag_range, event_matches):
    """
    Calculate the percentage of events in dataset that were matched with
    a corresponding USGS event and ID by magnitude.
    Args:
        eqids (np.array):
            Earthquake IDs of target events to be cross-referenced
        magnitudes (np.array):
            Magnitudes of target events to be cross-referenced.
        mag_range (list):
            Integer range of event magnitudes.
        event_matches (dictionary):
            Dictionary of data event IDs mapped to corresponding USGS event
            IDs (if found).
    Returns:
        mag_rates (list): List of event match percentages by magnitude.
    """
    mag_rates = []
    int_mags = magnitudes.astype(int)
    for mag in mag_range:
        mag_eqids = eqids[np.where(int_mags == mag)]
        mag_rate = 0
        if mag_eqids.size:
            mag_rate = match_percentage(mag_eqids, event_matches)
        mag_rates.append(mag_rate * 100)
    return mag_rates


def plot_match_rate_by_mag(project_name, mag_range, mag_rates):
    """
    Plot event match rate by magnitude.
    Args:
        project_name (string):
            Project or data source name.
        mag_range (list):
            Integer range of event magnitudes.
        mag_rates (list):
            List of percentages of events matched by magnitude.
    """
    plot_name = f"{project_name}_found_rate_by_mag.png"
    logging.info(f"Generating bar graph '{plot_name}'...")
    plt.bar(mag_range, mag_rates)
    plt.xlabel("Magnitude")
    plt.ylabel("Match Rate (%)")
    plt.title("""Event IDs to USGS Event IDs \n Match Rate by Magnitude""")
    plt.savefig(plot_name)
    logging.info("COMPLETE")


def write_summary(project_name, event_matches):
    """
    Write cross-referenced target event and USGS event attributes
    to excel file.
    Args:
        project_name (string):
            Project name or data source name.
        event_matches (dictionary):
            Map of target event ids to dictionary of matching
            USGS ID and other event attributes.
    """
    summary_data = {
        "project": [],
        "eqid": [],
        "magnitude": [],
        "latitude": [],
        "longitude": [],
        "time": [],
        "usgs_id": [],
        "usgs_magnitude": [],
        "usgs_latitude": [],
        "usgs_longitude": [],
        "usgs_time": [],
    }
    summary_data["project"] = project_name
    summary_data["eqid"] = event_matches.keys()
    ignore_keys = ["project", "eqid"]
    for key in summary_data.keys() - ignore_keys:
        summary_data[key] = [val[key] for _, val in event_matches.items()]
    summary_data = pd.DataFrame(summary_data)
    summary_data.columns = [col.upper() for col in summary_data.columns]
    summary_data.to_excel(f"{project_name}_usgs_ids_cross_reference.xlsx", index=False)


def set_target(mag, time, lat, lon):
    """
    Map time, mag, and location values of target event to a dictionary.
    Args:
        mag (float):
            Target event magnitude.
        time (datetime):
            Target event time.
        lat (float):
            Target event latitude.
        lon (float):
            Target event longitude.
    Returns:
        targets (dictionary): Dictionary of target event magnitude,
        time, and location values.
    """
    target = {"mag": mag, "time": time, "lat": lat, "lon": lon}
    return target


def set_buffer(target):
    """
    Map time, mag, and distance buffers for event query and error
    calculation to a dictionary.
    Args:
        target (dictionary):
            Dictionary of target event mag, time, and
            location values.
    Returns:
        buffer (dictionary): Dictionary of time, magnitude,
        and distance buffers.
    """
    if target["time"].strftime("%M:%S") == "00:00":
        DELTA_HOUR = 24
    time_buffer = datetime.timedelta(hours=DELTA_HOUR)
    # Search radius scaled by target event magnitude
    distance_buffer = DIST_SCALER * target["mag"]
    buffer = {"mag": DELTA_MAG, "time": time_buffer, "dist": distance_buffer}
    return buffer


def find_events(target, buffer):
    """
    Libcomcat query for potential matching events to the target.
    Args:
        target (dictionary):
            Dictionary of target event mag, time, and
            location values.
        buffer (dictionary): Dictionary of time, magnitude,
            and distance buffers.
    Returns:
        usgs_events (list): List of Libcomcat SummaryEvents.
    """
    url = SEARCH_TEMPLATE
    params = {
        "starttime": (target["time"] - buffer["time"]).strftime(TIMEFMT),
        "endtime": (target["time"] + buffer["time"]).strftime(TIMEFMT),
        "latitude": target["lat"],
        "longitude": target["lon"],
        "maxradiuskm": buffer["dist"],
        "maxmagnitude": target["mag"] + buffer["mag"],
        "minmagnitude": target["mag"] - buffer["mag"],
    }
    response = requests.get(url, params=params)
    usgs_events = []
    for feature in response.json()["features"]:
        event = Event(
            feature["id"],
            datetime.fromutctimestamp(feature["properties"]["time"] / 1000),
            feature["geometry"]["coordinates"][1],
            feature["geometry"]["coordinates"][0],
            feature["geometry"]["coordinates"][2],
            feature["properties"]["mag"],
        )
        usgs_events.append(event)

    return usgs_events


def calculate_error(event, buffer, target):
    """
    Find the squared distance, time, and magnitude error between a event
    and a target event.
    Args:
        event (SummaryEvent):
            Libcomcat summary of event attributes.
        buffer (dictionary):
            Dictionary of time, magnitude, and distance buffers.
        target (dictionary):
            Dictionary of target event mag, time, and
            location values.
    Returns:
        total_error (float): Float (0-3) giving the total error
        between the proposed matching event and the target event.
    """
    mag_error = np.abs(event.magnitude - target["mag"]) / buffer["mag"]
    time_error = (
        np.abs((event.time - target["time"]).total_seconds())
        / buffer["time"].total_seconds()
    )
    dist_error = np.sqrt(
        (event.latitude - target["lat"]) ** 2 + (event.longitude - target["lon"]) ** 2
    ) / (COORD_KM_SCALER * buffer["dist"])
    total_error = mag_error + time_error + dist_error
    return total_error


def match_percentage(eqids, event_matches):
    """
    Calculate the percentage of events in dataset that were matched with
    a corresponding USGS event and ID.
    Args:
        eqids (np.array):
            Array of target event (non-usgs) IDs.
        event_matches (dictionary):
            Map of target event ids to dictionary of matching
            USGS ID and other event attributes.
    Returns:
        rate (float): Percent (0 to 1) of events matched.
    """
    eqids = np.unique(eqids)
    rate = sum([bool(event_matches[eqid]["usgs_id"]) for eqid in eqids]) / len(eqids)
    return rate
