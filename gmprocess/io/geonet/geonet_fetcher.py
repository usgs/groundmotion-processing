# stdlib imports
from datetime import timedelta, datetime
import tempfile
import os.path
import io
import urllib
import ftplib
import logging
import shutil

# third party imports
import pytz
import numpy as np
import requests
from openquake.hazardlib.geo.geodetic import geodetic_distance
from obspy.core.utcdatetime import UTCDateTime
import pandas as pd

# local imports
from gmprocess.io.fetcher import _get_first_value
from gmprocess.io.geonet.core import read_geonet
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.config import get_config


CATBASE = "https://quakesearch.geonet.org.nz/csv?bbox=163.95996,-49.18170,182.63672,-32.28713&startdate=%s&enddate=%s"
GEOBASE = "ftp://ftp.geonet.org.nz/strong/processed/[YEAR]/[MONTH]/"
TIMEFMT = "%Y-%m-%dT%H:%M:%S"
NZTIMEDELTA = 2  # number of seconds allowed between GeoNet catalog time and
# event timestamp on FTP site
NZCATWINDOW = 5 * 60  # number of seconds to search around in GeoNet EQ catalog
KM2DEG = 1 / 111.0

# default values for this fetcher
# if None specified in constructor, AND no parameters specified in
# config, then use these.
RADIUS = 100  # kilometers
DT = 16  # seconds
DDEPTH = 30  # km
DMAG = 0.3

# NOTE - this class is currently disabled, as GNS is at the time of
# this writing on a path to shutting down their FTP service in favor
# of their FDSN service. To re-enable it, uncomment the line below
# and comment the one inheriting from object.
# class GeoNetFetcher(DataFetcher):


class GeoNetFetcher(object):
    # this announces to the world the valid bounds for this fetcher.
    BOUNDS = [158.555, 192.656, -51.553, -26.809]

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
        """Create a GeoNetFetcher instance.

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
                (Optional) username for site.
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

        if "fetchers" in config:
            if "GeoNetFetcher" in config["fetchers"]:
                fetch_cfg = config["fetchers"]["GeoNetFetcher"]
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
        start_time = self.time - timedelta(seconds=3600)
        end_time = self.time + timedelta(seconds=3600)

        tpl = (start_time.strftime(TIMEFMT), end_time.strftime(TIMEFMT))
        url = CATBASE % tpl
        req = requests.get(url)
        logging.debug("GeoNet search url: %s", str(url))
        logging.debug("GeoNet search response code: %s", req.status_code)
        data = req.text
        f = io.StringIO(data)
        df = pd.read_csv(f, parse_dates=["origintime"])
        f.close()
        # some of the column names have spaces in them
        cols = df.columns
        newcols = {}
        for col in cols:
            newcol = col.strip()
            newcols[col] = newcol
        df = df.rename(columns=newcols)
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
                "mag": row["magnitude"],
            }
            events.append(eventdict)

        if solve and len(events) > 1:
            event = self.solveEvents(events)
            events = [event]

        return events

    def retrieveData(self, event_dict):
        """Retrieve data from GeoNet FTP, turn into StreamCollection.

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
        etime = event_dict["time"]
        neturl = GEOBASE.replace("[YEAR]", str(etime.year))
        monthstr = etime.strftime("%m_%b")
        neturl = neturl.replace("[MONTH]", monthstr)
        urlparts = urllib.parse.urlparse(neturl)
        ftp = ftplib.FTP(urlparts.netloc)
        ftp.login()  # anonymous
        dirparts = urlparts.path.strip("/").split("/")
        for d in dirparts:
            try:
                ftp.cwd(d)
            except ftplib.error_perm as msg:
                raise Exception(msg)

        # cd to the desired output folder
        os.chdir(rawdir)
        datafiles = []

        # we cannot depend on the time given to us by the GeoNet catalog to
        # match the directory name on the FTP site, so we must do a secondary
        # matching.
        dirlist = ftp.nlst()
        fname = _match_closest_time(etime, dirlist)

        # create the event folder name from the time we got above
        # fname = etime.strftime('%Y-%m-%d_%H%M%S')

        try:
            ftp.cwd(fname)
        except ftplib.error_perm:
            msg = 'Could not find an FTP data folder called "%s". Returning.' % (
                urllib.parse.urljoin(neturl, fname)
            )
            raise Exception(msg)

        dirlist = ftp.nlst()
        for volume in dirlist:
            if volume.startswith("Vol1"):
                ftp.cwd(volume)
                if "data" not in ftp.nlst():
                    ftp.cwd("..")
                    continue

                ftp.cwd("data")
                flist = ftp.nlst()
                for ftpfile in flist:
                    if not ftpfile.endswith("V1A"):

                        continue
                    localfile = os.path.join(os.getcwd(), ftpfile)
                    if localfile in datafiles:
                        continue
                    datafiles.append(localfile)
                    f = open(localfile, "wb")
                    logging.info(f"Retrieving remote file {ftpfile}...\n")
                    ftp.retrbinary(f"RETR {ftpfile}", f.write)
                    f.close()
                ftp.cwd("..")
                ftp.cwd("..")

        ftp.quit()
        streams = []
        for dfile in datafiles:
            logging.info(f"Reading GeoNet file {dfile}...")
            try:
                tstreams = read_geonet(dfile)
                streams += tstreams
            except BaseException as e:
                fmt = (
                    'Failed to read GeoNet file "%s" due to error "%s". ' "Continuing."
                )
                tpl = (dfile, str(e))
                logging.warn(fmt % tpl)

        if self.rawdir is None:
            shutil.rmtree(rawdir)

        if self.stream_collection:
            stream_collection = StreamCollection(
                streams=streams, drop_non_free=self.drop_non_free
            )
            return stream_collection
        else:
            return None


def _match_closest_time(etime, dirlist):
    timefmt = "%Y-%m-%d_%H%M%S"
    etimes = [np.datetime64(datetime.strptime(dirname, timefmt)) for dirname in dirlist]
    etime = np.datetime64(etime)
    dtimes = np.abs(etimes - etime)

    new_etime = etimes[dtimes.argmin()]
    newtime = datetime.strptime(str(new_etime)[0:19], TIMEFMT)
    fname = newtime.strftime("%Y-%m-%d_%H%M%S")
    return fname
