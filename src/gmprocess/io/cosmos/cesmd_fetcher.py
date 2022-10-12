# stdlib imports
from datetime import datetime, timedelta
import logging


# third party imports
import pytz
from obspy.core.utcdatetime import UTCDateTime
import numpy as np

# local imports
from gmprocess.io.fetcher import DataFetcher, _get_first_value
from gmprocess.io.read import read_data
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.config import get_config
from gmprocess.io.cosmos.cesmd_search import (
    get_records,
    get_metadata,
    get_stations_dataframe,
)

# default values for this fetcher
# if None specified in constructor, AND no parameters specified in
# config, then use these.
STATION_RADIUS = 100  # kilometers
EQ_RADIUS = 10
EQ_DT = 10  # seconds
DDEPTH = 30  # km
DMAG = 0.3

MAX_STATIONS = 200

STATION_TYPE = "Ground"
PROCESS_TYPE = "raw"

URL_ERROR_CODE = 200  # if we get this from a request, we're good

TIMEFMT = "%Y-%m-%d %H:%M:%S"


class CESMDFetcher(DataFetcher):
    # this announces to the world the valid bounds for this fetcher.
    BOUNDS = [-180, 180, -90, 90]

    def __init__(
        self,
        time,
        lat,
        lon,
        depth,
        magnitude,
        email=None,
        process_type="raw",
        station_type="Ground",
        eq_radius=None,
        eq_dt=None,
        station_radius=None,
        rawdir=None,
        config=None,
        drop_non_free=True,
        stream_collection=True,
    ):
        """Create a CESMDFetcher instance.

        Download strong motion records from the CESMD site:
        https://strongmotioncenter.org/wserv/records/builder/

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
            email (str):
                email address for CESMD site.
            process_type (str):
                One of 'raw' or 'processed'.
            station_type (str):
                One of "Array", "Ground", "Building", "Bridge", "Dam",
                "Tunnel", "Wharf", "Other"
            eq_radius (float):
                Earthquake search radius (km).
            eq_dt (float):
                Earthquake search time window (sec).
            station_radius (float):
                Station search radius (km).
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
        cfg_eq_radius = None
        cfg_station_radius = None
        cfg_eq_dt = None
        cfg_email = None
        cfg_station_type = None
        cfg_process_type = None
        if "fetchers" in config:
            if "CESMDFetcher" in config["fetchers"]:
                fetch_cfg = config["fetchers"]["CESMDFetcher"]
                if "eq_radius" in fetch_cfg:
                    cfg_eq_radius = float(fetch_cfg["eq_radius"])
                if "station_radius" in fetch_cfg:
                    cfg_station_radius = float(fetch_cfg["station_radius"])
                if "dt" in fetch_cfg:
                    cfg_eq_dt = float(fetch_cfg["eq_dt"])
                if "email" in fetch_cfg:
                    cfg_email = fetch_cfg["email"]
                if "process_type" in fetch_cfg:
                    cfg_process_type = fetch_cfg["process_type"]
                if "station_type" in fetch_cfg:
                    cfg_station_type = fetch_cfg["station_type"]

        radius = _get_first_value(eq_radius, cfg_eq_radius, EQ_RADIUS)
        station_radius = _get_first_value(
            station_radius, cfg_station_radius, STATION_RADIUS
        )
        eq_dt = _get_first_value(eq_dt, cfg_eq_dt, EQ_DT)

        station_type = _get_first_value(station_type, cfg_station_type, STATION_TYPE)
        process_type = _get_first_value(process_type, cfg_process_type, PROCESS_TYPE)

        # for CESMD, user (email address) is required
        if email is None:
            # check to see if those values are configured
            if cfg_email:
                email = cfg_email
            else:
                fmt = "Email address is required to retrieve CESMD data."
                raise Exception(fmt)

        if email == "EMAIL":
            fmt = (
                "Email address is required to retrieve CESMD\n"
                "data. This tool can download data from the CESMD\n"
                "website. However, for this to work you will first need \n"
                "to register your email address using this website:\n"
                "https://strongmotioncenter.org/cgi-bin/CESMD/register.pl\n"
                "Then create a custom config file by running the gmsetup\n"
                "program, and edit the fetchers:CESMDFetcher section\n"
                "to use your email address."
            )
            raise Exception(fmt)

        self.metadata = None
        self.email = email
        self.process_type = process_type
        self.station_type = station_type
        tz = pytz.UTC
        if isinstance(time, UTCDateTime):
            time = time.datetime
        self.time = tz.localize(time)
        self.lat = lat
        self.lon = lon
        self.radius = radius
        self.station_radius = station_radius
        self.eq_dt = eq_dt
        self.rawdir = rawdir
        self.depth = depth
        self.magnitude = magnitude
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
        try:
            metadata = get_metadata(
                eqlat=self.lat,
                eqlon=self.lon,
                eqtime=self.time,
                abandoned=False,
                station_type=self.station_type,
                eqtimewindow=self.eq_dt,  # seconds
                eqradius=self.radius,  # km
                station_radius=self.station_radius,
            )
        except BaseException:
            return []

        tmp_events = metadata["results"]["events"]

        events = []
        idlist = []
        for event in tmp_events:
            tevent = {}
            # sometimes the metadata request returns duplicate events
            # strip those out here
            if event["id"] in idlist:
                continue
            idlist.append(event["id"])
            tevent["time"] = datetime.strptime(event["time"], "%Y-%m-%d %H:%M:%S")
            tevent["lat"] = event["latitude"]
            tevent["lon"] = event["longitude"]
            tevent["depth"] = event["depth"]
            tevent["mag"] = event["mag"]
            events.append(tevent.copy())

        if solve and len(events) > 1:
            event = self.solveEvents(events)
            events = [event]
        self.metadata = metadata

        return events

    def retrieveData(self, event_dict):
        """Retrieve data from CESMD, turn into StreamCollection.

        Args:
            event (dict):
                Best dictionary matching input event, fields as above
                in return of getMatchingEvents().

        Returns:
            StreamCollection: StreamCollection object.
        """
        if self.metadata is None:
            raise Exception("Must call getMatchingEvents() first.")

        # get matching event in metadata
        has_event = False
        for event in self.metadata["results"]["events"]:
            if event["time"] == event_dict["time"].strftime(TIMEFMT):
                has_event = True
                nstations = self.metadata["count"]
                break

        if not has_event:
            raise Exception("Could not find matching event.")

        starttime = self.time - timedelta(seconds=self.eq_dt // 2)
        endtime = self.time + timedelta(seconds=self.eq_dt // 2)

        if nstations < MAX_STATIONS:
            try:
                (_, datafiles) = get_records(
                    self.rawdir,
                    self.email,
                    unpack=True,
                    event_latitude=self.lat,
                    event_longitude=self.lon,
                    event_radius=self.radius,
                    process_level=self.process_type,
                    group_by="event",
                    max_station_dist=self.station_radius,
                    station_type=self.station_type,
                    startdate=starttime,
                    enddate=endtime,
                )
            except BaseException as ex:
                eqfmt = "M%.1f %s"
                eqdesc = eqfmt % (
                    self.magnitude,
                    self.time.strftime("%Y-%m-%d %H:%M:%S"),
                )
                if "404" in str(ex):
                    logging.info(f"Could not find data records for {eqdesc}")
                else:
                    logging.info(f"Unplanned exception getting records for {eqdesc}")
                return []
        else:
            # web service has a maximum number of stations you're allowed to
            # fetch (note that this may not be the same as the number of files)
            # so we're splitting up the stations by distance and downloading
            # them in chunks.

            # the stations are grouped a little oddly in the results of
            # the metadata - there are a number of "event" entries, all
            # with the same ID, and they each contain some collection
            # of stations. We want all of those stations, so we need to
            # iterate over the "events" and each station within them.
            dataframe = get_stations_dataframe(self.metadata)
            distances = sorted(dataframe["epidist"].to_numpy())
            nchunks = int(np.ceil(len(distances) / MAX_STATIONS))
            distance_chunks = np.array_split(distances, nchunks)
            datafiles = []
            for chunk in distance_chunks:
                mindist = chunk[0]
                maxdist = chunk[-1]
                try:
                    (_, tfiles) = get_records(
                        self.rawdir,
                        self.email,
                        unpack=True,
                        event_latitude=self.lat,
                        event_longitude=self.lon,
                        event_radius=self.radius,
                        process_level=self.process_type,
                        group_by="event",
                        min_station_dist=mindist,
                        max_station_dist=maxdist,
                        station_type=self.station_type,
                        startdate=starttime,
                        enddate=endtime,
                    )
                except BaseException as gpe:
                    eqfmt = "M%.1f %s"
                    eqdesc = eqfmt % (
                        self.magnitude,
                        self.time.strftime("%Y-%m-%d %H:%M:%S"),
                    )
                    if "404" in str(gpe):
                        fmt = (
                            "Could not find data records for %s "
                            "between %.1f km and %.1f km"
                        )
                        logging.info(fmt % (eqdesc, mindist, maxdist))
                    else:
                        logging.warning(
                            f"Unplanned exception getting records for {eqdesc}"
                        )
                    continue
                datafiles += tfiles

        if self.stream_collection:
            streams = []
            for dfile in datafiles:
                logging.info(f"Reading CESMD file {dfile}...")
                try:
                    streams += read_data(dfile)
                except BaseException as ex:
                    logging.info(f'Could not read {dfile}: error "{str(ex)}"')

            stream_collection = StreamCollection(
                streams=streams, drop_non_free=self.drop_non_free
            )
            return stream_collection
        else:
            return None
