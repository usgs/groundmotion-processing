#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import json
from datetime import datetime

import pandas as pd
import pytz

from gmprocess.utils.event import get_event_object, ScalarEvent


def get_events(eventids, textfile, eventinfo, directory, outdir=None):
    """Find the list of events.

    Args:
        eventids (list or None):
            List of ComCat event IDs.
        textfile (str or None):
            Path to text file containing event IDs or info.
        eventinfo (list or None):
            List containing:
                - id Any string, no spaces.
                - time Any ISO-compatible date/time string.
                - latitude Latitude in decimal degrees.
                - longitude Longitude in decimal degrees.
                - depth Depth in kilometers.
                - magnitude Earthquake magnitude.
        directory (str):
            Path to a directory containing event subdirectories, each
            containing an event.json file, where the ID in the json file
            matches the subdirectory containing it.
        outdir (str):
            Output directory.

    Returns:
        list: ScalarEvent objects.

    """
    events = []
    if eventids is not None:
        # Get list of events from directory if it has been provided
        tevents = []
        if directory is not None:
            tevents = events_from_directory(directory)
        elif outdir is not None:
            tevents = events_from_directory(outdir)
        eventidlist = [event.id for event in tevents]
        for eventid in eventids:
            try:
                idx = eventidlist.index(eventid)
                event = tevents[idx]
            except ValueError:
                # This connects to comcat to get event, does not check for a
                # local json file
                event = get_event_object(eventid)
            events.append(event)
    elif textfile is not None:
        events = parse_event_file(textfile)
    elif eventinfo is not None:
        eid = eventinfo[0]
        time = eventinfo[1]
        lat = float(eventinfo[2])
        lon = float(eventinfo[3])
        dep = float(eventinfo[4])
        mag = float(eventinfo[5])
        mag_type = str(eventinfo[6])
        event = ScalarEvent()
        event.fromParams(eid, time, lat, lon, dep, mag, mag_type)
        events = [event]
    elif directory is not None:
        events = events_from_directory(directory)
    elif outdir is not None:
        events = events_from_directory(outdir)

    # "events" elements are None if an error occurred, e.g., bad event id is specified.
    events = [e for e in events if e is not None]

    return events


def events_from_directory(dir):
    events = []
    eventfiles = get_event_files(dir)
    if len(eventfiles):
        events = read_event_json_files(eventfiles)
    else:
        eventids = [f for f in os.listdir(dir) if not f.startswith(".")]
        for eventid in eventids:
            try:
                event = get_event_object(eventid)
                events.append(event)

                # If the event ID has been updated, make sure to rename
                # the source folder and issue a warning to the user
                if event.id != eventid:
                    old_dir = os.path.join(dir, eventid)
                    new_dir = os.path.join(dir, event.id)
                    os.rename(old_dir, new_dir)
                    logging.warn(f"Directory {old_dir} has been renamed to {new_dir}.")
            except BaseException:
                logging.warning(f"Could not get info for event id: {eventid}")

    return events


def get_event_files(directory):
    """Get list of event.json files found underneath a data directory.

    Args:
        directory (str):
            Path to directory containing input raw data, where
            subdirectories must be event directories containing
            event.json files, where the id in that file matches
            the directory under which it is found.
    Returns:
        List of event.json files.
    """
    eventfiles = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name == "event.json":
                fullname = os.path.join(root, name)
                eventfiles.append(fullname)
    return eventfiles


def parse_event_file(eventfile):
    """Parse text file containing basic event information.

    Files can contain:
        - one column, in which case that column
          contains ComCat event IDs.
        - Six columns, in which case those columns should be:
          - id: any string (no spaces)
          - time: Any ISO standard for date/time.
          - lat: Earthquake latitude in decimal degrees.
          - lon: Earthquake longitude in decimal degrees.
          - depth: Earthquake longitude in kilometers.
          - magnitude: Earthquake magnitude.

    NB: THERE SHOULD NOT BE ANY HEADERS ON THIS FILE!

    Args:
        eventfile (str):
            Path to event text file

    Returns:
        list: ScalarEvent objects constructed from list of event information.

    """
    df = pd.read_csv(eventfile, sep=",", header=None)
    _, ncols = df.shape
    events = []
    if ncols == 1:
        df.columns = ["eventid"]
        for _, row in df.iterrows():
            event = get_event_object(row["eventid"])
            events.append(event)
    elif ncols == 6:
        df.columns = [
            "id",
            "time",
            "lat",
            "lon",
            "depth",
            "magnitude",
        ]
        df["time"] = pd.to_datetime(df["time"])
        for _, row in df.iterrows():
            rowdict = row.to_dict()
            event = get_event_object(rowdict)
            events.append(event)
    else:
        return None
    return events


def read_event_json_files(eventfiles):
    """Read event.json file and return ScalarEvent object.

    Args:
        eventfiles (list):
            Event.json files to be read.
    Returns:
        list: ScalarEvent objects.

    """
    events = []
    for eventfile in eventfiles:
        with open(eventfile, "rt", encoding="utf-8") as f:
            event = json.load(f)
            try:
                origintime = datetime.fromtimestamp(
                    event["properties"]["time"] / 1000.0, pytz.utc
                )
                evdict = {
                    "id": event["id"],
                    "time": origintime.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                    "lat": event["geometry"]["coordinates"][1],
                    "lon": event["geometry"]["coordinates"][0],
                    "depth": event["geometry"]["coordinates"][2],
                    "magnitude": event["properties"]["mag"],
                    "magnitude_type": event["properties"]["magType"],
                }
                event = get_event_object(evdict)

            except BaseException:
                event = get_event_object(event)

            events.append(event)
    return events
