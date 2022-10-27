#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import importlib
import inspect
import logging
import pathlib

# local imports
from .fetcher import DataFetcher
from gmprocess.utils.config import get_config
from gmprocess.io.utils import _walk

SKIP_MODS = [
    "fetcher.py",
    "global_fetcher.py",
    "nga.py",
    "read.py",
    "read_directory.py",
    "report.py",
    "seedname.py",
    "stream.py",
    "utils.py",
]


def fetch_data(
    time,
    lat,
    lon,
    depth,
    magnitude,
    config=None,
    rawdir=None,
    drop_non_free=True,
    stream_collection=True,
):
    """Retrieve data using any DataFetcher subclass.

    Args:
        time (datetime):
            Origin time.
        lat (float):
            Origin latitude.
        lon (float):
            Origin longitude.
        depth (float):
            Origin depth.
        magnitude (float):
            Origin magnitude.
        config (dict):
            Project config dictionary.
        rawdir (str):
            Path to location where raw data will be stored. If not specified, raw data
            will be deleted.
        drop_non_free (bool):
            Option to ignore non-free-field (borehole, sensors on structures, etc.)
        stream_collection (bool):
            Construct and return a StreamCollection instance?

     Returns:
        StreamCollection: StreamCollection object.
    """
    if config is None:
        config = get_config()

    tfetchers = find_fetchers(lat, lon)

    # Remove fetchers if they are not present in the conf file
    fetchers = {
        k: v
        for k, v in tfetchers.items()
        if k in config["fetchers"]
        if config["fetchers"][k]["enabled"]
    }
    for fname in fetchers.keys():
        if fname not in config["fetchers"]:
            del fetchers[fname]

    instances = []
    errors = []
    for fetchname, fetcher in fetchers.items():
        try:
            fetchinst = fetcher(
                time,
                lat,
                lon,
                depth,
                magnitude,
                config=config,
                rawdir=rawdir,
                drop_non_free=drop_non_free,
                stream_collection=stream_collection,
            )
        except BaseException as e:
            fmt = 'Could not instantiate Fetcher %s, due to error\n "%s"'
            tpl = (fetchname, str(e))
            msg = fmt % tpl
            logging.warn(msg)
            errors.append(msg)
            continue
        xmin, xmax, ymin, ymax = fetchinst.BOUNDS
        if (xmin < lon < xmax) and (ymin < lat < ymax):
            instances.append(fetchinst)

    efmt = "%s M%.1f (%.4f,%.4f)"
    etpl = (time, magnitude, lat, lon)
    esummary = efmt % etpl
    streams = []
    for fetcher in instances:
        if "FDSN" in str(fetcher):
            tstreams = fetcher.retrieveData()
            if streams:
                streams = streams + tstreams
            else:
                streams = tstreams

        else:
            events = fetcher.getMatchingEvents(solve=True)
            if not len(events):
                msg = "No event matching %s found by class %s"
                logging.warn(msg % (esummary, str(fetcher)))
                continue
            tstreams = fetcher.retrieveData(events[0])
            if streams:
                streams = streams + tstreams
            else:
                streams = tstreams

        if streams is None:
            streams = []

    return (streams, errors)


def find_fetchers(lat, lon):
    """Create a dictionary of classname:class to be used in main().

    Args:
        lat (float):
            Origin latitude.
        lon (float):
            Origin longitude.

    Returns:
        dict: Dictionary of classname:class where each class is a subclass of
        shakemap.coremods.base.CoreModule.
    """

    fetchers = {}
    root = pathlib.Path(__file__).parent
    for mod_file in _walk(root):
        if str(mod_file).find("__") >= 0:
            continue
        mod_tuple = mod_file.parts[mod_file.parts.index("gmprocess") :]
        if mod_tuple[-1] in SKIP_MODS:
            continue
        mod_name = ".".join(mod_tuple)
        if mod_name.endswith(".py"):
            mod_name = mod_name[:-3]
        mod = importlib.import_module(mod_name)
        for name, obj in inspect.getmembers(mod):
            if name == "DataFetcher":
                continue
            if inspect.isclass(obj) and issubclass(obj, DataFetcher):
                xmin, xmax, ymin, ymax = obj.BOUNDS
                if (xmin < lon < xmax) and (ymin < lat < ymax):
                    fetchers[name] = obj
    return fetchers
