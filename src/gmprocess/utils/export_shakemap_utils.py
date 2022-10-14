#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import re
import json
import logging
from datetime import datetime
from collections import OrderedDict

import numpy as np
import prov.model

from gmprocess.core.stationtrace import NS_SEIS, _get_person_agent, _get_software_agent
from gmprocess.io.cosmos.core import BUILDING_TYPES
from gmprocess.utils.constants import EVENT_TIMEFMT, COMPONENTS, UNITS
from gmprocess.metrics.station_summary import XML_UNITS


def create_json(
    workspace,
    event,
    event_dir,
    label,
    config=None,
    expanded_imts=False,
    gmprocess_version="unknown",
):
    """Create JSON file for ground motion parametric data.

    Args:
        workspace (StreamWorkspace):
            gmrpocess StreamWorkspace object.
        event (ScalarEvent):
            Event object.
        event_dir (str or pathlib.Path):
            Event directory.
        label (str):
            Processing label.
        config (dict):
            Configuration options.
        expanded_imts (bool):
            Use expanded IMTs. Currently this only means all the SA that have
            been computed, plus PGA and PGV (if computed). Could eventually
            expand for other IMTs also.
        gmprocess_version (str):
            gmprocess version.
    """
    event_dir = Path(event_dir)

    features = []

    station_features = []

    streams = workspace.getStreams(event.id, labels=[label], config=config)
    npassed = 0
    for stream in streams:
        if stream.passed:
            npassed += 1
    if not npassed:
        logging.info("No strong motion data found that passes tests. Exiting.")
        return (None, None, 0)

    # Creating a new provenance document and filling in the software
    # information for every trace can be slow, so here we create a
    # base provenance document that will be copied and used as a template
    base_prov = prov.model.ProvDocument()
    base_prov.add_namespace(*NS_SEIS)
    base_prov = _get_person_agent(base_prov, config)
    base_prov = _get_software_agent(base_prov, gmprocess_version)

    nfeatures = 0
    for stream in streams:
        if not stream.passed:
            continue

        # Station is the feature, and properties contain
        # channel dictionary with all information about the metrics
        feature = OrderedDict()
        properties = OrderedDict()
        properties["network_code"] = stream[0].stats.network
        properties["station_code"] = stream[0].stats.station
        # properties['location_code'] = stream[0].stats.location
        properties["name"] = stream[0].stats.standard["station_name"]
        properties["provider"] = stream[0].stats.standard["source"]
        properties["instrument"] = stream[0].stats.standard["instrument"]
        properties["source_format"] = stream[0].stats.standard["source_format"]
        struct_desc = stream[0].stats.standard["structure_type"]
        struct_type = _get_cosmos_code(struct_desc)
        properties["station_housing"] = {
            "cosmos_code": struct_type,
            "description": struct_desc,
        }
        nfeatures += 1

        metrics = workspace.getStreamMetrics(
            event.id,
            properties["network_code"],
            properties["station_code"],
            label,
            config=config,
        )

        if metrics is None:
            continue

        coordinates = [
            stream[0].stats.coordinates.longitude,
            stream[0].stats.coordinates.latitude,
            stream[0].stats.coordinates.elevation,
        ]

        station_feature = get_station_feature(
            stream, metrics, coordinates, expanded_imts=expanded_imts
        )
        if station_feature is not None:
            station_features.append(station_feature)

        components = get_components(metrics, stream, config)
        properties["components"] = components

        provenance = {}

        for trace in stream:
            channel = trace.stats.channel

            # get trace provenance
            provthing = trace.getProvenanceDocument(base_prov=base_prov)
            provjson = provthing.serialize(format="json")
            provenance_dict = json.loads(provjson)
            provenance[channel] = provenance_dict

        properties["provenance"] = provenance
        feature["geometry"] = {"type": "Point", "coordinates": coordinates}
        feature["type"] = "Feature"

        properties = replace_nan(properties)

        feature["properties"] = properties
        features.append(feature)

    event_dict = {
        "id": event.id,
        "time": event.time.strftime(EVENT_TIMEFMT),
        "location": "",
        "latitude": event.latitude,
        "longitude": event.longitude,
        "depth": event.depth,
        "magnitude": event.magnitude,
    }
    feature_dict = {
        "type": "FeatureCollection",
        "software": {"name": "gmprocess", "version": gmprocess_version},
        "process_time": datetime.utcnow().strftime(EVENT_TIMEFMT) + "Z",
        "event": event_dict,
        "features": features,
    }

    station_feature_dict = {"type": "FeatureCollection", "features": station_features}
    stationfile = event_dir / f"{event.id}_groundmotions_dat.json"
    # debugging
    iterdict(station_feature_dict)
    # end debugging
    with open(stationfile, "wt") as f:
        json.dump(station_feature_dict, f, allow_nan=False)

    jsonfile = event_dir / f"{event.id}_metrics.json"
    with open(jsonfile, "wt") as f:
        json.dump(feature_dict, f, allow_nan=False)

    return (jsonfile, stationfile, nfeatures)


def iterdict(d):
    for k, v in d.items():
        if isinstance(v, dict):
            iterdict(v)
        else:
            if isinstance(v, float) and np.isnan(v):
                print(k, ":", v)


def _get_cosmos_code(desc):
    rev_types = dict(map(reversed, BUILDING_TYPES.items()))
    if desc in rev_types:
        return rev_types[desc]
    else:
        return 51


def get_station_feature(stream, metrics, coordinates, expanded_imts=False):
    scode = f"{stream[0].stats.network}.{stream[0].stats.station}"
    station_feature = OrderedDict()
    station_properties = OrderedDict()
    station_feature["type"] = "Feature"
    station_feature["id"] = scode
    station_properties["name"] = stream[0].stats.standard["station_name"]

    station_properties["code"] = stream[0].stats.station
    station_properties["network"] = stream[0].stats.network
    station_properties["distance"] = metrics.distances["epicentral"]
    # station_properties['source'] = stream[0].stats.standard['source']
    station_properties["source"] = stream[0].stats.network
    station_channels = []
    station_channel_names = ["H1", "H2", "Z"]

    if expanded_imts:
        imts = list(
            set([i[0] for i in metrics.pgms.index.to_numpy() if i[0].startswith("SA")])
        )
        imt_lower = [s.lower() for s in imts]
        imt_units = [UNITS["SA"]] * len(imts)
        if "PGA" in metrics.pgms.index:
            imts.append("PGA")
            imt_lower.append("pga")
            imt_units.append(UNITS["PGA"])
        if "PGV" in metrics.pgms.index:
            imts.append("PGV")
            imt_lower.append("pgv")
            imt_units.append(UNITS["PGV"])
        station_amps = {k: v for k, v in zip(imts, zip(imt_lower, imt_units))}
    else:
        station_amps = {
            "SA(0.300)": ("sa(0.3)", UNITS["SA"]),
            "SA(1.000)": ("sa(1.0)", UNITS["SA"]),
            "SA(3.000)": ("sa(3.0)", UNITS["SA"]),
            "PGA": ("pga", UNITS["PGA"]),
            "PGV": ("pgv", UNITS["PGV"]),
        }

    channel_dict = metrics.channel_dict

    for channel_name in station_channel_names:
        station_channel = OrderedDict()
        if channel_name in metrics.components:
            station_channel["name"] = channel_dict[channel_name]
            station_amplitudes = []
            for gm_imt, station_tuple in station_amps.items():
                imt_value = metrics.get_pgm(gm_imt, channel_name)
                station_amplitude = OrderedDict()
                station_amplitude["name"] = station_tuple[0]
                station_amplitude["ln_sigma"] = 0
                station_amplitude["flag"] = 0
                station_amplitude["value"] = imt_value
                station_amplitude["units"] = station_tuple[1]
                station_amplitudes.append(station_amplitude.copy())
            station_channel["amplitudes"] = station_amplitudes
            station_channels.append(station_channel)
    if len(station_channels):
        station_properties["channels"] = station_channels
    else:
        return None
    station_feature["properties"] = station_properties
    station_feature["geometry"] = {"type": "Point", "coordinates": coordinates}
    return station_feature


def get_components(metrics, stream, config):
    FLOAT_MATCH = r"[0-9]*\.[0-9]*"
    components = OrderedDict()
    for imc in metrics.components:
        if imc in ["H1", "H2", "Z"]:
            imtlist = COMPONENTS["CHANNELS"]
        else:
            imtlist = COMPONENTS[imc]
        measures = OrderedDict()
        spectral_values = []
        spectral_periods = []
        fourier_amplitudes = []
        fourier_periods = []
        for imt in metrics.imts:
            if imt.startswith("FAS"):
                imtstr = "FAS"
            elif imt.startswith("SA"):
                imtstr = "SA"
            else:
                imtstr = imt
            if imtstr not in imtlist:
                continue
            imt_value = metrics.get_pgm(imt, imc)
            if np.isnan(imt_value):
                imt_value = "null"
            if imt.startswith("SA"):
                period = float(re.search(FLOAT_MATCH, imt).group())
                spectral_values.append(imt_value)
                spectral_periods.append(period)
            elif imt.startswith("FAS"):
                period = float(re.search(FLOAT_MATCH, imt).group())
                fourier_amplitudes.append(imt_value)
                fourier_periods.append(period)
            elif imt.startswith("DURATION"):
                # TODO - Make interval something retrievable from metrics
                units = XML_UNITS[imt.lower()]
                measures[imt] = {"value": imt_value, "units": units, "interval": "5-95"}
            else:
                units = XML_UNITS[imt.lower()]
                measures[imt] = {"value": imt_value, "units": units}

        if imc in ["H1", "H2", "Z"]:
            imcname = metrics.channel_dict[imc]
            measures["as_recorded"] = True
            ttrace = stream.select(component=imcname[-1])
            azimuth = np.nan
            dip = np.nan
            if len(ttrace):
                trace = ttrace[0]
                sampling_rate = trace.stats.sampling_rate
                location_code = trace.stats.location
                peak_acc = trace.data.max()
                start = trace.stats.starttime
                delta = trace.stats.delta
                idx = np.where([trace.data >= peak_acc])[1][0]
                peak_pga_time = (start + (delta * idx)).strftime(EVENT_TIMEFMT)
                vel_trace = trace.copy()
                vel_trace.integrate(config)
                peak_vel = vel_trace.data.max()
                start = vel_trace.stats.starttime
                delta = vel_trace.stats.delta
                idx = np.where([vel_trace.data >= peak_vel])[1][0]
                peak_pgv_time = (start + (delta * idx)).strftime(EVENT_TIMEFMT)
                if "horizontal_orientation" in trace.stats.standard:
                    azimuth = trace.stats.standard["horizontal_orientation"]
                dip = trace.stats.standard["vertical_orientation"]
            else:
                sampling_rate = np.nan
                location_code = ""
                peak_pga_time = np.nan
                peak_pgv_time = np.nan

            measures["samples_per_second"] = sampling_rate
            measures["location_code"] = location_code
            measures["peak_pga_time"] = peak_pga_time
            measures["peak_pgv_time"] = peak_pgv_time
            measures["azimuth"] = azimuth
            measures["dip"] = dip
        else:
            imcname = imc
            measures["as_recorded"] = False
        components[imcname] = measures
        if len(spectral_values):
            units = XML_UNITS["sa"]
            damping = metrics.damping
            sa_dict = {"units": units, "damping": damping, "method": "absolute"}
            sa_dict["values"] = spectral_values
            sa_dict["periods"] = spectral_periods
            components[imcname]["SA"] = sa_dict
        if len(fourier_amplitudes):
            units = XML_UNITS["fas"]
            fas_dict = {
                "units": units,
                "values": fourier_amplitudes,
                "periods": fourier_periods,
            }
            components[imcname]["FAS"] = fas_dict
    return components


def replace_nan(properties):
    # replace nans in any field in input dictionary with a "null" string.
    for key, value in properties.items():
        if isinstance(value, (float, np.floating)):
            if np.isnan(value):
                properties[key] = "null"
        elif isinstance(value, dict):
            properties[key] = replace_nan(value)
    return properties
