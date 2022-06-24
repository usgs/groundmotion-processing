# stdlib imports
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
import shutil
import tempfile
import os.path
import logging

# third party imports
import logging
import pytz
import numpy as np
import requests
from bs4 import BeautifulSoup
from openquake.hazardlib.geo.geodetic import geodetic_distance
from obspy.core.utcdatetime import UTCDateTime
import pandas as pd

# local imports
from gmprocess.io.fetcher import DataFetcher, _get_first_value
from gmprocess.io.nsmn.core import read_nsmn
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.config import get_config


SEARCH_URL = "http://kyhdata.deprem.gov.tr/2K/kyhdata_v4.php?dst=TU9EVUxFX05BTUU9ZWFydGhxdWFrZSZNT0RVTEVfVEFTSz1zZWFyY2g%3D"

EQ_FORM_DATA = {
    "from_day": "",
    "from_month": "",
    "from_year": "",
    "from_md": "",
    "to_md": "",
    "to_day": "",
    "to_month": "",
    "to_year": "",
    "from_ml": "",
    "to_ml": "",
    "from_epi_lat": "34.00",
    "to_epi_lat": "43.00",
    "from_ms": "",
    "to_ms": "",
    "from_epi_lon": "24.0",
    "to_epi_lon": "45.82",
    "from_mw": "",
    "to_mw": "",
    "from_depth": "",
    "to_depth": "",
    "from_mb": "",
    "to_mb": "",
}

# 2019/03/13-13:48:00.00
TIMEFMT = "%Y-%m-%dT%H:%M:%S"

# default values for this fetcher
# if None specified in constructor, AND no parameters specified in
# config, then use these.
RADIUS = 100  # kilometers
DT = 16  # seconds
DDEPTH = 30  # km
DMAG = 0.3


class TurkeyFetcher(DataFetcher):
    # this announces to the world the valid bounds for this fetcher.
    BOUNDS = [25.664, 46.67, 34.132, 43.555]

    def __init__(
        self,
        time,
        lat,
        lon,
        depth,
        magnitude,
        user=None,
        password=None,
        radius=100,
        dt=16,
        ddepth=30,
        dmag=0.3,
        rawdir=None,
        config=None,
        drop_non_free=True,
    ):
        """Create a TurkeyFetcher instance.

        Download Turkish strong motion data from the Turkish NSMN site:
        http://kyhdata.deprem.gov.tr/2K/kyhdata_v4.php

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
            radius (float):
                Search radius (km).
            dt (float):
                Search time window (sec).
            ddepth (float):
                Search depth window (km).
            dmag (float):
                Search magnitude window (magnitude units).
            rawdir (str):
                Path to location where raw data will be stored. If not
                specified, raw data will be deleted.
            config (dict):
                Dictionary containing configuration.
                If None, retrieve global config.
            drop_non_free (bool):
                Option to ignore non-free-field (borehole, sensors on
                structures, etc.)
        """
        # what values do we use for search thresholds?
        # In order of priority:
        # 1) Not-None values passed in constructor
        # 2) Configured values
        # 3) DEFAULT values at top of the module
        if config is None:
            config = get_config()
        cfg_radius = None
        cfg_dt = None
        cfg_ddepth = None
        cfg_dmag = None

        if "fetchers" in config:
            if "TurkeyFetcher" in config["fetchers"]:
                fetch_cfg = config["fetchers"]["TurkeyFetcher"]
                if "radius" in fetch_cfg:
                    cfg_radius = float(fetch_cfg["radius"])
                if "dt" in fetch_cfg:
                    cfg_dt = float(fetch_cfg["dt"])
                if "ddepth" in fetch_cfg:
                    cfg_ddepth = float(fetch_cfg["ddepth"])
                if "dmag" in fetch_cfg:
                    cfg_dmag = float(fetch_cfg["dmag"])

        radius = _get_first_value(radius, cfg_radius, RADIUS)
        dt = _get_first_value(dt, cfg_dt, DT)
        ddepth = _get_first_value(ddepth, cfg_ddepth, DDEPTH)
        dmag = _get_first_value(dmag, cfg_dmag, DMAG)

        tz = pytz.UTC
        if isinstance(time, UTCDateTime):
            time = time.datetime
        self.time = tz.localize(time)
        self.lat = lat
        self.lon = lon
        self.radius = radius
        self.dt = dt
        self.rawdir = rawdir
        self.depth = depth
        self.magnitude = magnitude
        self.ddepth = ddepth
        self.dmag = dmag
        self.drop_non_free = drop_non_free

    def getMatchingEvents(self, solve=True):
        """Return a list of dictionaries matching input parameters.

        Args:
            solve (bool):
                If set to True, then this method
                should return a list with a maximum of one event.

        Returns:
            list: List of event dictionaries, with fields:
                  - time Event time (UTC)
                  - lat Event latitude
                  - lon Event longitude
                  - depth Event depth
                  - mag Event magnitude
        """
        df = get_turkey_dataframe(self.time, 1)
        if df is None:
            return []
        lats = df["latitude"].to_numpy()
        lons = df["longitude"].to_numpy()
        etime = pd.Timestamp(self.time)
        dtimes = np.abs(df["origintime"] - etime)
        distances = geodetic_distance(self.lon, self.lat, lons, lats)
        didx = distances <= self.radius
        tidx = (dtimes <= np.timedelta64(int(self.dt), "s")).to_numpy()
        newdf = df[didx & tidx]
        events = []
        for idx, row in newdf.iterrows():
            eventdict = {
                "time": UTCDateTime(row["origintime"]),
                "lat": row["latitude"],
                "lon": row["longitude"],
                "depth": row["depth"],
                "url": row["url"],
                "mag": row["magnitude"],
            }
            events.append(eventdict)

        if solve and len(events) > 1:
            event = self.solveEvents(events)
            events = [event]

        return events

    def retrieveData(self, event_dict):
        """Retrieve data from NSMN, turn into StreamCollection.

        Args:
            event (dict):
                Best dictionary matching input event, fields as above
                in return of getMatchingEvents().

        Returns:
            StreamCollection: StreamCollection object.
        """
        rawdir = self.rawdir
        if self.rawdir is None:
            rawdir = tempfile.mkdtemp()
        else:
            if not os.path.isdir(rawdir):
                os.makedirs(rawdir)

        urlparts = urlparse(SEARCH_URL)
        req = requests.get(event_dict["url"])

        logging.debug("TurkeyFetcher event url: %s", str(event_dict["url"]))
        logging.debug("TurkeyFetcher event response code: %s", req.status_code)

        data = req.text
        soup = BeautifulSoup(data, features="lxml")
        table = soup.find_all("table", "tableType_01")[1]
        datafiles = []
        for row in table.find_all("tr"):
            if "class" in row.attrs:
                continue
            col = row.find_all("td", "coltype01")[0]
            href = col.contents[0].attrs["href"]
            station_id = col.contents[0].contents[0]
            station_url = urljoin("http://" + urlparts.netloc, href)
            req2 = requests.get(station_url)
            logging.debug("TurkeyFetcher station url: %s", str(station_url))
            logging.debug("TurkeyFetcher station response code: %s", req2.status_code)
            data2 = req2.text
            soup2 = BeautifulSoup(data2, features="lxml")
            center = soup2.find_all("center")[0]
            anchor = center.find_all("a")[0]
            href2 = anchor.attrs["href"]
            data_url = urljoin("http://" + urlparts.netloc, href2)
            req3 = requests.get(data_url)
            logging.debug("TurkeyFetcher data url: %s", str(data_url))
            logging.debug("TurkeyFetcher data response code: %s", req3.status_code)
            data = req3.text
            localfile = os.path.join(rawdir, f"{station_id}.txt")
            logging.info(f"Downloading Turkish data file {station_id}...")
            with open(localfile, "wt") as f:
                f.write(data)
            datafiles.append(localfile)

        streams = []
        for dfile in datafiles:
            logging.info(f"Reading datafile {dfile}...")
            streams += read_nsmn(dfile)

        if self.rawdir is None:
            shutil.rmtree(rawdir)

        stream_collection = StreamCollection(
            streams=streams, drop_non_free=self.drop_non_free
        )
        return stream_collection


def get_turkey_dataframe(time, dt):
    """Retrieve a dataframe of events from the NSMN site.

    Args:
        time (datetime): Earthquake origin time.
        dt (int): Number of days around origin time to search.

    Returns:
        DataFrame: Catalog of events with columns:
            - id Turkish Earthquake ID.
            - url URL where station data for this event can be downloaded.
            - origintime Earthquake origin time.
            - latitude Earthquake origin latitude.
            - longitude Earthquake origin longitude.
            - depth Earthquake origin depth.
            - magnitude Largest Turkish magnitude (from list of ML, MD, MS,
              MW, MB)
        or None if no events are found.

    """
    urlparts = urlparse(SEARCH_URL)
    url = SEARCH_URL
    params = EQ_FORM_DATA.copy()
    start_time = time - timedelta(days=dt)
    end_time = time + timedelta(days=dt)
    params["from_year"] = str(start_time.year)
    params["from_month"] = "%02i" % start_time.month
    params["from_day"] = "%02i" % start_time.day
    params["to_year"] = str(end_time.year)
    params["to_month"] = "%02i" % end_time.month
    params["to_day"] = "%02i" % end_time.day
    req = requests.post(url, params)
    logging.debug("TurkeyFetcher dataframe url: %s", str(url))
    logging.debug("TurkeyFetcher dataframe response code: %s", req.status_code)
    if req.status_code != 200:
        return None
    data = req.text
    soup = BeautifulSoup(data, features="lxml")
    all_table = soup.find_all("table", "tableType_01")
    if len(all_table):
        table = all_table[0]
        cols = [
            "id",
            "origintime",
            "latitude",
            "longitude",
            "depth",
            "magnitude",
            "url",
        ]
        df = pd.DataFrame(columns=cols)
        for row in table.find_all("tr"):
            if "class" in row.attrs and row.attrs["class"] == ["headerRowType_01"]:
                continue
            cols = row.find_all("td", "coltype01")
            href = cols[0].contents[0].attrs["href"]
            event_url = urljoin("http://" + urlparts.netloc, href)
            eid = cols[0].contents[0].contents[0]
            datestr = str(cols[1].contents[0])
            timestr = str(cols[2].contents[0])
            timestr = timestr[0:8]
            lat = float(str(cols[3].contents[0]))
            lon = float(str(cols[4].contents[0]))
            depth = float(str(cols[5].contents[0]))
            mags = []
            for i in range(6, 11):
                if len(cols[i].contents):
                    mag = float(str(cols[i].contents[0]))
                    mags.append(mag)
            mag = max(mags)
            time = datetime.strptime(datestr + "T" + timestr, TIMEFMT)
            time = pd.Timestamp(time).tz_localize("UTC")
            edict = {
                "id": eid,
                "url": event_url,
                "origintime": time,
                "latitude": lat,
                "longitude": lon,
                "depth": depth,
                "magnitude": mag,
            }
            df = df.append(edict, ignore_index=True)

        # make sure that origintime is actually a time
        df["origintime"] = pd.to_datetime(df["origintime"])
        return df
    else:
        return None
