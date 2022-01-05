#!/usr/bin/env python

# stdlib imports
import tarfile
import argparse
import pathlib

# third party imports
from obspy import read, read_inventory
import configobj

# local imports
from gmprocess.utils.event import get_event_object
from gmprocess.utils.download_utils import create_event_file, download_rupture_file


def main(args):
    CONF_PATH = pathlib.Path.home() / ".gmprocess"
    PROJECTS_FILE = CONF_PATH / "projects.conf"
    projects_conf = configobj.ConfigObj(str(PROJECTS_FILE), encoding="utf-8")
    project = projects_conf["project"]
    current_project = projects_conf["projects"][project]
    conf_parts = pathlib.PurePath(current_project["conf_path"]).parts
    data_parts = pathlib.PurePath(current_project["data_path"]).parts
    conf_path = CONF_PATH.joinpath(*conf_parts).resolve()
    data_path = CONF_PATH.joinpath(*data_parts).resolve()
    event_path = data_path / args.event
    raw_path = event_path / "raw"
    if not event_path.exists():
        event_path.mkdir()
        raw_path.mkdir()
    traces = read(args.seedfile)
    for trace in traces:
        network = trace.stats.network
        station = trace.stats.station
        channel = trace.stats.channel
        location = trace.stats.location
        starttime_str = trace.stats.starttime.strftime("%Y%m%dT%H%M%SZ")
        endtime_str = trace.stats.endtime.strftime("%Y%m%dT%H%M%SZ")
        fname = (
            f"{network}.{station}.{location}.{channel}__{starttime_str}__{endtime_str}"
        )
        filename = raw_path / fname
        trace.write(str(filename), format="MSEED")
    print(f"{len(traces)} channels written to {raw_path}.")
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
                if resp_name in responses:
                    old_inv = responses[resp_name]
                    new_channel = inventory.networks[0].stations[0].channels[0]
                    old_network = old_inv.networks[0]
                    old_station = old_network.stations[0]
                    old_station.channels.append(new_channel)
                else:
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
    desc = "Convert CWB data from web site into form ingestible by gmprocess."
    parser = argparse.ArgumentParser(description=desc)
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

    pargs = parser.parse_args()
    main(pargs)
