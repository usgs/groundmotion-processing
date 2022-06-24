#!/usr/bin/env python

# stdlib imports
import argparse
import sys
import json
import pathlib
import tarfile

# third party imports
import numpy as np
from obspy import read, read_inventory
import configobj

# local imports
from gmprocess.utils.event import get_event_object
from gmprocess.utils.download_utils import create_event_file, download_rupture_file


def read_stations():
    stationfile = pathlib.Path(__file__).parent / ".." / "data" / "GDMSstations.json"
    jdict = json.load(open(stationfile, "rt"))
    stations = {}
    for station in jdict:
        deployment = station[0]
        network = "TW"
        station_code = station[1]
        latitude = float(station[2])
        longitude = float(station[3])
        elevation = float(station[4])
        if np.isnan(elevation):
            elevation = 0.0
        station_dict = {
            "network": network,
            "deployment": deployment,
            "station": station_code,
            "latitude": latitude,
            "longitude": longitude,
            "elevation": elevation,
        }
        key = f"{network}.{station_code}"
        stations[key] = station_dict
    return stations


def main():
    desc = """Convert CWB data from web site into form ingestible by gmprocess.

    To obtain CWB strong motion data, create an account on the CWB GDMS-2020 website:

    https://gdmsn.cwb.gov.tw/index.php

    To retrieve strong motion response files:

    Click on the "Data" icon, then click on "Instrument Response". 

     - For "Output Format", choose "RESP file".
     - For "Network", choose "CWBSN".
     - For "Station", check "All Stations".
     - For "Location", choose "*" for all locations.
     - For "Channel", choose "HN?" for all strong motion stations.
     - For "Start Time (UTC)", enter a date before the event of interest.
     - For "End Time (UTC)", enter a date after the event of interest.
     - For "Label", enter any string that is descriptive to you.

     Click the "Submit" button, and you should see a "Success!" pop up.
     Next will be a screen showing a list of all of your downloads. Response data
     links should appear fairly quickly - click on the name of the generated gzipped
     "tarball" file to download it.

    To retrieve a strong motion data file:

    Click on the "Data" icon, then click on "Multi-Station Waveform Data". 

     - For "Output Format", choose "MiniSEED".
     - For "Network", choose "CWBSN".
     - For "Station", check "All Stations".
     - For "Location", choose "*" for all locations.
     - For "Channel", choose "HN?" for all strong motion stations.
     - For "Start Time (UTC)", enter a time 30 seconds before the origin time of 
       interest.
     - For "End Time (UTC)", enter a time 7 minutes after the origin time of interest.
     - For "Label", enter any string that is descriptive to you.

     Click the "Submit" button, and you should see a "Success!" pop up.
     Next will be a screen showing a list of all of your downloads. Data
     links will take a few minutes to process - click on the name of the generated 
     miniseed file to download it.

     Pass these files along with the ComCat ID as described below.
    """
    parser = argparse.ArgumentParser(
        description=desc,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "event",
        help="ComCat Event ID",
    )
    parser.add_argument(
        "seedfile",
        help="Miniseed file containing all relevant data",
    )
    parser.add_argument(
        "tarball",
        help="Tarball containing response files",
    )
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()

    stations = read_stations()
    CONF_PATH = pathlib.Path.home() / ".gmprocess"
    PROJECTS_FILE = CONF_PATH / "projects.conf"
    projects_conf = configobj.ConfigObj(str(PROJECTS_FILE), encoding="utf-8")
    project = projects_conf["project"]
    current_project = projects_conf["projects"][project]
    data_parts = pathlib.PurePath(current_project["data_path"]).parts
    data_path = CONF_PATH.joinpath(*data_parts).resolve()
    event_path = data_path / args.event
    raw_path = event_path / "raw"
    if not event_path.exists():
        event_path.mkdir()
        raw_path.mkdir()
    raw_stream = read(args.seedfile)
    # some of these files are returned from CWB web site in time chunks
    # using this merge method joins up all of the traces with the same
    # NSCL. Thanks Obspy!
    stream = raw_stream.merge(fill_value="interpolate", interpolation_samples=-1)
    for trace in stream:
        network = trace.stats.network
        station = trace.stats.station
        channel = trace.stats.channel
        location = trace.stats.location
        starttime_str = trace.stats.starttime.strftime("%Y%m%dT%H%M%SZ")
        endtime_str = trace.stats.endtime.strftime("%Y%m%dT%H%M%SZ")
        fname = (
            f"{network}.{station}.{location}.{channel}__"
            f"{starttime_str}__{endtime_str}.mseed"
        )
        filename = raw_path / fname
        trace.write(str(filename), format="MSEED")
    print(f"{len(stream)} channels written to {raw_path}.")
    responses = {}
    with tarfile.open(args.tarball, "r") as tarball:
        for member in tarball.getmembers():
            if member.isdir():
                continue
            with tarball.extractfile(member) as fh:
                inventory = read_inventory(fh)
                network = inventory.networks[0]
                netcode = network.code
                station = network.stations[0]
                stacode = station.code
                resp_name = f"{netcode}.{stacode}"
                if resp_name not in stations:
                    print(
                        f"No station coordinates available for station {resp_name}. Skipping."
                    )
                    continue
                latitude = stations[resp_name]["latitude"]
                longitude = stations[resp_name]["longitude"]
                elevation = stations[resp_name]["elevation"]
                if resp_name in responses:
                    old_inventory = responses[resp_name]
                    old_station = old_inventory.networks[0].stations[0]
                    new_station = inventory.networks[0].stations[0]
                    new_channel = new_station.channels[0]
                    new_channel.latitude = latitude
                    new_channel.longitude = longitude
                    new_channel.elevation = elevation
                    old_station.channels.append(new_channel)
                else:
                    for station in inventory.networks[0].stations:
                        station.latitude = latitude
                        station.longitude = longitude
                        station.elevation = elevation
                        for channel in station.channels:
                            channel.latitude = latitude
                            channel.longitude = longitude
                            channel.elevation = elevation
                    responses[resp_name] = inventory
    for resp_name, response in responses.items():
        fname = resp_name + ".xml"
        filename = raw_path / fname
        response.write(str(filename), format="stationxml")
    print(f"{len(responses)} station responses written to {raw_path}.")
    scalar_event = get_event_object(args.event)
    create_event_file(scalar_event, str(event_path))
    event_file = event_path / "event.json"
    msg = f"Created event file at {event_file}."
    if not event_file.exists():
        msg = f"Error: Failed to create {event_file}."
    print(msg)
    download_rupture_file(args.event, str(event_path))
    rupture_file = event_path / "rupture.json"
    msg = f"Created rupture file at {rupture_file}."
    if not rupture_file.exists():
        msg = f"Error: Failed to create {rupture_file}."
    print(msg)


if __name__ == "__main__":
    main()
