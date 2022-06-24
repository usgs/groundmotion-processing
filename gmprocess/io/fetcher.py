#!/usr/bin/env python
# -*- coding: utf-8 -*-

# third party imports
from obspy.core.utcdatetime import UTCDateTime
from openquake.hazardlib.geo.geodetic import geodetic_distance
import numpy as np


class DataFetcher(object):
    def __init__(
        self,
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
        """Create a DataFetcher instance.

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
                Dictionary containing configuration.
                If None, retrieve global config.
            rawdir (str):
                Path to location where raw data will be stored.
                If not specified, raw data will be deleted.
            drop_non_free (bool):
                Option to ignore non-free-field (borehole, sensors on
                structures, etc.)
            stream_collection (bool):
                Construct and return a StreamCollection instance?
        """
        # this method should be implemented in the child class
        pass

    def getMatchingEvents(self, solve=True):
        """
        For appropriate fetchers, return a list of dictionaries matching
        input parameters.

        Args:
            solve (bool):
                If set to True, then this method should return a list with
                a maximum of one event.

        Returns:
            list: List of event dictionaries, with fields:
                  - time Event time (UTC)
                  - lat Event latitude
                  - lon Event longitude
                  - depth Event depth
                  - mag Event magnitude
        """
        pass

    def retrieveData(self, event):
        """Retrieve data from remote source, turn into StreamCollection.

        Args:
            event (dict):
                Best dictionary matching input event, fields as above
                in return of getMatchingEvents().

        Returns:
            StreamCollection: StreamCollection object.
        """
        pass

    def solveEvents(self, events):
        """Reduce a list of events down to one that best matches the input.

        Args:
            events (list):
                List of dictionaries with fields:
                - time Event time (UTC)
                - lat Event latitude
                - lon Event longitude
                - depth Event depth
                - mag Event magnitude

        Returns:
            dict: Event dictionary (see above)
        """
        edict = {
            "time": UTCDateTime(self.time),
            "lat": self.lat,
            "lon": self.lon,
            "depth": self.depth,
            "mag": self.magnitude,
        }

        zmin = 9e12
        minevent = None
        for i in range(0, len(events)):
            event = events[i]
            ddist = geodetic_distance(
                edict["lon"], edict["lat"], event["lon"], event["lat"]
            )
            ddist_norm = ddist / self.radius
            dt_norm = np.abs(edict["time"] - event["time"]) / self.dt
            ddepth_norm = np.abs(edict["depth"] - event["depth"]) / self.ddepth
            dmag_norm = np.abs(edict["mag"] - event["mag"]) / self.dmag
            ddsq = np.power(ddist_norm, 2)
            dtsq = np.power(dt_norm, 2)
            dzsq = np.power(ddepth_norm, 2)
            dmsq = np.power(dmag_norm, 2)
            z = np.sqrt(ddsq + dtsq + dzsq + dmsq)
            if z < zmin:
                zmin = z
                minevent = event

        return minevent


def _get_first_value(val1, val2, val3):
    # return first not-None value from this list
    if val1 is not None:
        return val1
    if val2 is not None:
        return val2
    return val3
