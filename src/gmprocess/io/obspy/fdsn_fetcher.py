# stdlib imports
import tempfile
import os.path
import logging
import glob
import sys

# third party imports
import pytz
from obspy.core.utcdatetime import UTCDateTime
from obspy.clients.fdsn.header import URL_MAPPINGS, FDSNException
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.mass_downloader import (
    CircularDomain,
    RectangularDomain,
    Restrictions,
    MassDownloader,
)

# local imports
from gmprocess.io.fetcher import DataFetcher
from gmprocess.io.obspy.core import read_obspy
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.config import get_config


OBSPY_LOGGER = "obspy.clients.fdsn.mass_downloader"

GEONET_ARCHIVE_DAYS = 7 * 86400
GEONET_ARCHIVE_URL = "http://service.geonet.org.nz"
GEO_NET_ARCHIVE_KEY = "GEONET"
GEONET_REALTIME_URL = "http://service-nrt.geonet.org.nz"


class FDSNFetcher(DataFetcher):
    BOUNDS = [-180, 180, -90, 90]

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
        """Create an FDSNFetcher instance.

        Download waveform data from the all available FDSN sites
        using the Obspy mass downloader functionality.

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
        if config is None:
            config = get_config()

        tz = pytz.UTC
        if isinstance(time, UTCDateTime):
            time = time.datetime
        self.time = tz.localize(time)
        self.lat = lat
        self.lon = lon
        self.depth = depth
        self.magnitude = magnitude
        self.config = config
        self.rawdir = rawdir
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
        pass

    def retrieveData(self):
        """Retrieve data from many FDSN services, turn into StreamCollection.

        Args:
            event (dict):
                Best dictionary matching input event, fields as above
                in return of getMatchingEvents().

        Returns:
            StreamCollection: StreamCollection object.
        """
        # Bail out if FDSNFetcher not configured
        if "FDSNFetcher" not in self.config["fetchers"]:
            return

        fdsn_conf = self.config["fetchers"]["FDSNFetcher"]
        rawdir = self.rawdir

        if self.rawdir is None:
            rawdir = tempfile.mkdtemp()
        else:
            if not os.path.isdir(rawdir):
                os.makedirs(rawdir)

        # use the mass downloader to retrieve data of interest from any FSDN
        # service.
        origin_time = UTCDateTime(self.time)

        # The Obspy mass downloader has it's own logger - grab that stream
        # and write it to our own log file
        ldict = logging.Logger.manager.loggerDict
        if OBSPY_LOGGER in ldict:
            root = logging.getLogger()
            fhandler = root.handlers[0]
            obspy_logger = logging.getLogger(OBSPY_LOGGER)
            try:
                obspy_stream_handler = obspy_logger.handlers[0]
                obspy_logger.removeHandler(obspy_stream_handler)
            except IndexError:
                pass

            obspy_logger.addHandler(fhandler)

        # Circular domain around the epicenter.
        if fdsn_conf["domain"]["type"] == "circular":
            dconf = fdsn_conf["domain"]["circular"]
            if dconf["use_epicenter"]:
                dconf["latitude"] = self.lat
                dconf["longitude"] = self.lon
            dconf.pop("use_epicenter")
            domain = CircularDomain(**dconf)
        elif fdsn_conf["domain"]["type"] == "rectangular":
            dconf = fdsn_conf["domain"]["rectangular"]
            domain = RectangularDomain(**dconf)
        else:
            raise ValueError('Domain type must be either "circular" or "rectangular".')

        rconf = fdsn_conf["restrictions"]

        rconf["starttime"] = origin_time - rconf["time_before"]
        rconf["endtime"] = origin_time + rconf["time_after"]
        rconf.pop("time_before")
        rconf.pop("time_after")

        restrictions = Restrictions(**rconf)

        # For each of the providers, check if we have a username and password provided
        # in the config. If we do, initialize the client with the username and password.
        # Otherwise, use default initalization.
        providers = URL_MAPPINGS
        if "IRISPH5" in providers.keys():
            del providers["IRISPH5"]

        client_list = []
        for provider_str in providers.keys():
            if provider_str == GEO_NET_ARCHIVE_KEY:
                dt = UTCDateTime.utcnow() - UTCDateTime(self.time)
                if dt < GEONET_ARCHIVE_DAYS:
                    provider_str = GEONET_REALTIME_URL
            try:
                fdsn_config = self.config["fetchers"]["FDSNFetcher"]
                if provider_str in fdsn_config:
                    if logging.getLevelName(root.level) == "DEBUG":
                        client = Client(
                            provider_str,
                            user=fdsn_config[provider_str]["user"],
                            password=fdsn_config[provider_str]["password"],
                            debug=True,
                        )
                    else:
                        client = Client(
                            provider_str,
                            user=fdsn_config[provider_str]["user"],
                            password=fdsn_config[provider_str]["password"],
                        )
                else:
                    if logging.getLevelName(root.level) == "DEBUG":
                        client = Client(provider_str, debug=True)
                    else:
                        client = Client(provider_str)

                client_list.append(client)
            # If the FDSN service is down, then an FDSNException is raised
            except FDSNException:
                logging.warning(f"Unable to initalize client {provider_str}")
            except KeyError:
                logging.warning(f"Unable to initalize client {provider_str}")

        if len(client_list):
            for handler in root.handlers:
                if hasattr(handler, "baseFilename"):
                    log_file = getattr(handler, "baseFilename")
            if "log_file" in vars() or "log_file" in globals():
                sys.stdout = open(log_file, "a")
            # Pass off the initalized clients to the Mass Downloader
            if logging.getLevelName(root.level) == "DEBUG":
                mdl = MassDownloader(providers=client_list, debug=True)
            else:
                try:
                    # Need to turn off built in logging for ObsPy>=1.3.0
                    mdl = MassDownloader(providers=client_list, configure_logging=False)
                except TypeError:
                    # For ObsPy<1.3.0 the configure_logging parameter doesn't exist
                    mdl = MassDownloader(providers=client_list)

            logging.info("Downloading new MiniSEED files...")
            # The data will be downloaded to the ``./waveforms/`` and
            # ``./stations/`` folders with automatically chosen file names.
            mdl.download(
                domain, restrictions, mseed_storage=rawdir, stationxml_storage=rawdir
            )
            if "log_file" in vars() or "log_file" in globals():
                sys.stdout.close()

            if self.stream_collection:
                seed_files = glob.glob(os.path.join(rawdir, "*.mseed"))
                streams = []
                for seed_file in seed_files:
                    try:
                        tstreams = read_obspy(seed_file, self.config)
                    except BaseException as e:
                        tstreams = None
                        fmt = 'Could not read seed file %s - "%s"'
                        logging.info(fmt % (seed_file, str(e)))
                    if tstreams is None:
                        continue
                    else:
                        streams += tstreams

                stream_collection = StreamCollection(
                    streams=streams, drop_non_free=self.drop_non_free
                )
                return stream_collection
            else:
                return None
