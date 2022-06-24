# stdlib imports
from datetime import datetime, timedelta
import re
from collections import OrderedDict
import tempfile
import os.path
import tarfile
import glob
import shutil
import logging
import urllib

# third party imports
import pytz
import numpy as np
import requests
from bs4 import BeautifulSoup
from openquake.hazardlib.geo.geodetic import geodetic_distance
from obspy.core.utcdatetime import UTCDateTime

# local imports
from gmprocess.io.fetcher import DataFetcher, _get_first_value
from gmprocess.io.knet.core import read_knet
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.config import get_config


JST_OFFSET = 9 * 3600  # Japan standard time is UTC + 9
SEARCH_URL = "http://www.kyoshin.bosai.go.jp/cgi-bin/kyoshin/quick/list_eqid_en.cgi?1+YEAR+QUARTER"
RETRIEVE_URL = "http://www.kyoshin.bosai.go.jp/cgi-bin/kyoshin/auth/makearc"

# http://www.kyoshin.bosai.go.jp/cgi-bin/kyoshin/auth/makearc?formattype=A&eqidlist=20180330081700%2C20180330000145%2C20180330081728%2C1%2C%2Fkyoshin%2Fpubdata%2Fall%2F1comp%2F2018%2F03%2F20180330081700%2F20180330081700.all_acmap.png%2C%2Fkyoshin%2Fpubdata%2Fknet%2F1comp%2F2018%2F03%2F20180330081700%2F20180330081700.knt_acmap.png%2C%2Fkyoshin%2Fpubdata%2Fkik%2F1comp%2F2018%2F03%2F20180330081700%2F20180330081700.kik_acmap.png%2CHPRL&datanames=20180330081700%3Balldata&datakind=all

CGIPARAMS = OrderedDict()
CGIPARAMS["formattype"] = "A"
CGIPARAMS["eqidlist"] = ""
CGIPARAMS["datanames"] = ""
CGIPARAMS["alldata"] = None
CGIPARAMS["datakind"] = "all"

QUARTERS = {
    1: 1,
    2: 1,
    3: 1,
    4: 4,
    5: 4,
    6: 4,
    7: 7,
    8: 7,
    9: 7,
    10: 10,
    11: 10,
    12: 10,
}

# 2019/03/13-13:48:00.00
TIMEPAT = r"[0-9]{4}/[0-9]{2}/[0-9]{2}-[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{2}"
LATPAT = r"[0-9]{2}\.[0-9]{2}N"
LONPAT = r"[0-9]{3}\.[0-9]{2}E"
DEPPAT = "[0-9]{3}km"
MAGPAT = r"M[0-9]{1}\.[0-9]{1}"
TIMEFMT = "%Y/%m/%d-%H:%M:%S.%f"

# default values for this fetcher
# if None specified in constructor, AND no parameters specified in
# config, then use these.
RADIUS = 100  # kilometers
DT = 60  # seconds
DDEPTH = 30  # km
DMAG = 0.3

URL_ERROR_CODE = 200  # if we get this from a request, we're good

# create a dictionary of magnitudes and distances. These will be used with
# this fetcher to restrict the number of stations from Japan that are processed
# and stored. The distances are derived from an empirical analysis of active
# region earthquakes. In a small sample size, this seems to reduce the number
# of Japanese stations by roughly 25%.
MAGS = OrderedDict()
MAGS[5.5] = 122
MAGS[6.5] = 288
MAGS[7.5] = 621
MAGS[9.9] = 1065


class KNETFetcher(DataFetcher):
    # this announces to the world the valid bounds for this fetcher.
    BOUNDS = [127.705, 147.393, 29.428, 46.109]

    def __init__(
        self,
        time,
        lat,
        lon,
        depth,
        magnitude,
        user=None,
        password=None,
        radius=None,
        dt=None,
        ddepth=None,
        dmag=None,
        rawdir=None,
        config=None,
        drop_non_free=True,
        stream_collection=True,
    ):
        """Create a KNETFetcher instance.

        Download KNET/KikNet data from the Japanese NIED site:
        http://www.kyoshin.bosai.go.jp/cgi-bin/kyoshin/quick/list_eqid_en.cgi

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
            user (str):
                username for KNET/KikNET site.
            password (str):
                (Optional) password for site.
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
            stream_collection (bool):
                Construct and return a StreamCollection instance?

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
        cfg_user = None
        cfg_password = None
        if "fetchers" in config:
            if "KNETFetcher" in config["fetchers"]:
                fetch_cfg = config["fetchers"]["KNETFetcher"]
                if "radius" in fetch_cfg:
                    cfg_radius = float(fetch_cfg["radius"])
                if "dt" in fetch_cfg:
                    cfg_dt = float(fetch_cfg["dt"])
                if "ddepth" in fetch_cfg:
                    cfg_ddepth = float(fetch_cfg["ddepth"])
                if "dmag" in fetch_cfg:
                    cfg_dmag = float(fetch_cfg["dmag"])
                if "user" in fetch_cfg:
                    cfg_user = fetch_cfg["user"]
                if "password" in fetch_cfg:
                    cfg_password = fetch_cfg["password"]

        radius = _get_first_value(radius, cfg_radius, RADIUS)
        dt = _get_first_value(dt, cfg_dt, DT)
        ddepth = _get_first_value(ddepth, cfg_ddepth, DDEPTH)
        dmag = _get_first_value(dmag, cfg_dmag, DMAG)

        # for knet/kiknet, username/password is required
        if user is None or password is None:
            # check to see if those values are configured
            if cfg_user and cfg_password:
                user = cfg_user
                password = cfg_password
            else:
                fmt = "Username/password are required to retrieve KNET/KikNET data."
                raise Exception(fmt)

        if user == "USERNAME" or password == "PASSWORD":
            fmt = (
                "Username/password are required to retrieve KNET/KikNET\n"
                "data. This tool can download data from the Japanese NIED\n"
                "website. However, for this to work you will first need \n"
                "to obtain a username and password from this website:\n"
                "https://hinetwww11.bosai.go.jp/nied/registration/?LANG=en\n"
                "Then create a custom config file by running the gmsetup\n"
                "program, and edit the fetchers:KNETFetcher section\n"
                "to use your username and password."
            )
            raise Exception(fmt)

        # allow user to turn restrict stations on or off. Restricting saves
        # time, probably will not ignore significant data.
        self.restrict_stations = config["fetchers"]["KNETFetcher"]["restrict_stations"]

        self.user = user
        self.password = password
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
        self.jptime = self.time + timedelta(seconds=JST_OFFSET)
        self.drop_non_free = drop_non_free
        self.stream_collection = stream_collection

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
        jpyear = str(self.jptime.year)
        jpquarter = str(QUARTERS[self.jptime.month])
        if len(jpquarter) == 1:
            jpquarter = "0" + jpquarter
        url = SEARCH_URL.replace("YEAR", jpyear)
        url = url.replace("QUARTER", jpquarter)
        req = requests.get(url)
        logging.debug("KNET search url: %s", str(url))
        logging.debug("KNET search response code: %s", req.status_code)
        data = req.text
        soup = BeautifulSoup(data, features="lxml")
        select = soup.find("select")
        options = select.find_all("option")
        times = []
        lats = []
        lons = []
        depths = []
        mags = []
        values = []
        for option in options:
            if "Data not found" in option.text:
                break
            eventstr = option.contents[0]
            timestr = re.search(TIMEPAT, eventstr).group()
            latstr = re.search(LATPAT, eventstr).group()
            lonstr = re.search(LONPAT, eventstr).group()
            depstr = re.search(DEPPAT, eventstr).group()
            magstr = re.search(MAGPAT, eventstr).group()
            lat = float(latstr.replace("N", ""))
            lon = float(lonstr.replace("E", ""))
            depth = float(depstr.replace("km", ""))
            mag = float(magstr.replace("M", ""))
            etime = datetime.strptime(timestr, TIMEFMT)
            times.append(np.datetime64(etime))
            lats.append(lat)
            lons.append(lon)
            depths.append(depth)
            mags.append(mag)
            values.append(option.get("value"))

        events = []
        if not len(times):
            return events

        times = np.array(times)
        lats = np.array(lats)
        lons = np.array(lons)
        depths = np.array(depths)
        mags = np.array(mags)
        values = np.array(values)
        distances = geodetic_distance(self.lon, self.lat, lons, lats)
        didx = distances <= self.radius
        jptime = np.datetime64(self.jptime)
        # dtimes is in microseconds
        dtimes = np.abs(jptime - times)
        tidx = dtimes <= np.timedelta64(int(self.dt), "s")
        etimes = times[didx & tidx]
        elats = lats[didx & tidx]
        elons = lons[didx & tidx]
        edepths = depths[didx & tidx]
        emags = mags[didx & tidx]
        evalues = values[didx & tidx]

        for etime, elat, elon, edep, emag, evalue in zip(
            etimes, elats, elons, edepths, emags, evalues
        ):
            jtime = UTCDateTime(str(etime))
            utime = jtime - JST_OFFSET
            edict = {
                "time": utime,
                "lat": elat,
                "lon": elon,
                "depth": edep,
                "mag": emag,
                "cgi_value": evalue,
            }
            events.append(edict)

        if solve and len(events) > 1:
            event = self.solveEvents(events)
            events = [event]

        return events

    def retrieveData(self, event_dict):
        """Retrieve data from NIED, turn into StreamCollection.

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

        cgi_value = event_dict["cgi_value"]
        firstid = cgi_value.split(",")[0]
        dtime = event_dict["time"]
        fname = dtime.strftime("%Y%m%d%H%M%S") + ".tar"

        localfile = os.path.join(rawdir, fname)

        url = RETRIEVE_URL
        payload = {
            "formattype": ["A"],
            "eqidlist": cgi_value,
            "datanames": f"{firstid};alldata",
            "datakind": ["all"],
        }
        logging.info(f"Downloading Japanese data into {localfile}...")
        req = requests.get(url, params=payload, auth=(self.user, self.password))
        logging.debug("KNET download url: %s", str(url))
        logging.debug("KNET download response code: %s", req.status_code)

        if req.status_code != URL_ERROR_CODE:
            raise urllib.error.HTTPError(req.text)
        else:
            with open(localfile, "wb") as f:
                for chunk in req:
                    f.write(chunk)
        logging.info(f"Finished downloading into {localfile}...")

        # open the tarball, extract the kiknet/knet gzipped tarballs
        tar = tarfile.open(localfile)
        names = tar.getnames()
        tarballs = []
        for name in names:
            if "img" in name:
                continue
            ppath = os.path.join(rawdir, name)
            tarballs.append(ppath)
            tar.extract(name, path=rawdir)
        tar.close()

        # remove the tar file we downloaded
        os.remove(localfile)

        subdirs = []
        for tarball in tarballs:
            tar = tarfile.open(tarball, mode="r:gz")
            if "kik" in tarball:
                subdir = os.path.join(rawdir, "kiknet")
            else:
                subdir = os.path.join(rawdir, "knet")
            subdirs.append(subdir)
            tar.extractall(path=subdir)
            tar.close()
            os.remove(tarball)

        for subdir in subdirs:
            gzfiles = glob.glob(os.path.join(subdir, "*.gz"))
            for gzfile in gzfiles:
                os.remove(gzfile)

        if self.stream_collection:
            streams = []
            for subdir in subdirs:
                datafiles = glob.glob(os.path.join(subdir, "*.*"))
                for dfile in datafiles:
                    logging.info(f"Reading KNET/KikNet file {dfile}...")
                    streams += read_knet(dfile)

            if self.rawdir is None:
                shutil.rmtree(rawdir)

            # Japan gives us a LOT of data, much of which is not useful as it
            # is too far away. Use the following distance thresholds for
            # different magnitude ranges, and trim streams that are beyond this
            # distance.
            threshold_distance = None
            if self.restrict_stations:
                for mag, tdistance in MAGS.items():
                    if self.magnitude < mag:
                        threshold_distance = tdistance
                        break

            newstreams = []
            for stream in streams:
                slat = stream[0].stats.coordinates.latitude
                slon = stream[0].stats.coordinates.longitude
                distance = geodetic_distance(self.lon, self.lat, slon, slat)
                if distance <= threshold_distance:
                    newstreams.append(stream)

            stream_collection = StreamCollection(
                streams=newstreams, drop_non_free=self.drop_non_free
            )
            return stream_collection
        else:
            return None
