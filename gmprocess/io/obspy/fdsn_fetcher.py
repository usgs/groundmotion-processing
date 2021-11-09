# stdlib imports
import tempfile
import os.path
import logging
import glob
import sys

# third party imports
import logging
import pytz
from obspy.core.utcdatetime import UTCDateTime
from obspy.clients.fdsn.header import URL_MAPPINGS, FDSNException
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.mass_downloader import \
    CircularDomain, Restrictions, MassDownloader

# local imports
from gmprocess.io.fetcher import DataFetcher, _get_first_value
from gmprocess.io.obspy.core import read_obspy
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.config import get_config


# default values for this fetcher
# if None specified in constructor, AND no parameters specified in
# config, then use these.
RADIUS = 4  # dd
TIME_BEFORE = 10  # seconds
TIME_AFTER = 420  # seconds
CHANNELS = ["HN[ZNE]"]  # default to only get strong motion stations
EXCLUDE_NETWORKS = ['SY']
EXCLUDE_STATIONS = []
REJECT_CHANNELS_WITH_GAPS = True
MINIMUM_LENGTH = 0.1
SANITIZE = True
MINIMUM_INTERSTATION_DISTANCE_IN_M = 0.0
NETWORK = '*'

URL_ERROR_CODE = 200  # if we get this from a request, we're good

OBSPY_LOGGER = "obspy.clients.fdsn.mass_downloader"

GEONET_ARCHIVE_DAYS = 7 * 86400
GEONET_ARCHIVE_URL = 'http://service.geonet.org.nz'
GEO_NET_ARCHIVE_KEY = 'GEONET'
GEONET_REALTIME_URL = 'http://service-nrt.geonet.org.nz'


class FDSNFetcher(DataFetcher):
    def __init__(self, time, lat, lon, depth, magnitude,
                 radius=None, time_before=None, time_after=None, channels=None,
                 rawdir=None, config=None, drop_non_free=True,
                 stream_collection=True):
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
            radius (float):
                Search radius (km).
            time_before (float):
                Seconds before arrival time (sec).
            time_after (float):
                Seconds after arrival time (sec).
            rawdir (str):
                Path to location where raw data will be stored.
                If not specified, raw data will be deleted.
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
        cfg_time_before = None
        cfg_time_after = None
        cfg_channels = None
        exclude_networks = EXCLUDE_NETWORKS
        exclude_stations = EXCLUDE_STATIONS
        reject_channels_with_gaps = REJECT_CHANNELS_WITH_GAPS
        minimum_length = MINIMUM_LENGTH
        sanitize = SANITIZE
        minimum_interstation_distance_in_m = MINIMUM_INTERSTATION_DISTANCE_IN_M
        network = NETWORK
        if 'fetchers' in config:
            if 'FDSNFetcher' in config['fetchers']:
                fetch_cfg = config['fetchers']['FDSNFetcher']
                if 'radius' in fetch_cfg:
                    cfg_radius = float(fetch_cfg['radius'])
                if 'time_before' in fetch_cfg:
                    cfg_time_before = float(fetch_cfg['time_before'])
                if 'time_after' in fetch_cfg:
                    cfg_time_after = float(fetch_cfg['time_after'])
                if 'channels' in fetch_cfg:
                    cfg_channels = fetch_cfg['channels']
                if 'exclude_networks' in fetch_cfg:
                    exclude_networks = fetch_cfg['exclude_networks']
                if 'exclude_stations' in fetch_cfg:
                    exclude_stations = fetch_cfg['exclude_stations']
                if 'reject_channels_with_gaps' in fetch_cfg:
                    reject_channels_with_gaps = \
                        fetch_cfg['reject_channels_with_gaps']
                if 'minimum_length' in fetch_cfg:
                    minimum_length = fetch_cfg['minimum_length']
                if 'sanitize' in fetch_cfg:
                    sanitize = fetch_cfg['sanitize']
                if 'minimum_interstation_distance_in_m' in fetch_cfg:
                    minimum_interstation_distance_in_m = \
                        fetch_cfg['minimum_interstation_distance_in_m']
                if 'network' in fetch_cfg:
                    network = fetch_cfg['network']
        radius = _get_first_value(radius, cfg_radius, RADIUS)
        time_before = _get_first_value(time_before,
                                       cfg_time_before,
                                       TIME_BEFORE)
        time_after = _get_first_value(time_after,
                                      cfg_time_after,
                                      TIME_AFTER)
        channels = _get_first_value(channels, cfg_channels, CHANNELS)

        tz = pytz.UTC
        if isinstance(time, UTCDateTime):
            time = time.datetime
        self.time = tz.localize(time)
        self.lat = lat
        self.lon = lon
        self.radius = radius
        self.time_before = time_before
        self.time_after = time_after
        self.rawdir = rawdir
        self.depth = depth
        self.magnitude = magnitude
        self.channels = channels
        self.network = network

        self.exclude_networks = exclude_networks
        self.exclude_stations = exclude_stations
        self.reject_channels_with_gaps = reject_channels_with_gaps
        self.minimum_length = minimum_length
        self.sanitize = sanitize
        self.minimum_interstation_distance_in_m = \
            minimum_interstation_distance_in_m

        self.drop_non_free = drop_non_free
        self.stream_collection = stream_collection
        self.BOUNDS = [-180, 180, -90, 90]
        self.config = config

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
        if 'FDSNFetcher' not in self.config['fetchers']:
            return
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
            obspy_stream_handler = obspy_logger.handlers[0]
            obspy_logger.removeHandler(obspy_stream_handler)
            obspy_logger.addHandler(fhandler)

        # Circular domain around the epicenter.
        domain = CircularDomain(latitude=self.lat, longitude=self.lon,
                                minradius=0, maxradius=self.radius)

        min_dist = self.minimum_interstation_distance_in_m
        restrictions = Restrictions(
            # Define the temporal bounds of the waveform data.
            starttime=origin_time - self.time_before,
            endtime=origin_time + self.time_after,
            network=self.network, station='*',
            location='*',
            location_priorities=['*'],
            reject_channels_with_gaps=self.reject_channels_with_gaps,
            # Any trace that is shorter than 95 % of the
            # desired total duration will be discarded.
            minimum_length=self.minimum_length,
            sanitize=self.sanitize,
            minimum_interstation_distance_in_m=min_dist,
            exclude_networks=self.exclude_networks,
            exclude_stations=self.exclude_stations,
            channel_priorities=self.channels)

        # For each of the providers, check if we have a username and password
        # provided in the config. If we do, initialize the client with the
        # username and password. Otherwise, use default initalization.
        client_list = []
        for provider_str in URL_MAPPINGS.keys():
            if provider_str == GEO_NET_ARCHIVE_KEY:
                dt = UTCDateTime.utcnow() - UTCDateTime(self.time)
                if dt < GEONET_ARCHIVE_DAYS:
                    provider_str = GEONET_REALTIME_URL
            try:
                fdsn_config = self.config['fetchers']['FDSNFetcher']
                if provider_str in fdsn_config:
                    if logging.getLevelName(root.level) == 'DEBUG':
                        client = Client(
                            provider_str,
                            user=fdsn_config[provider_str]['user'],
                            password=fdsn_config[provider_str]['password'],
                            debug=True)
                    else:
                        client = Client(
                            provider_str,
                            user=fdsn_config[provider_str]['user'],
                            password=fdsn_config[provider_str]['password'])
                else:
                    if logging.getLevelName(root.level) == 'DEBUG':
                        client = Client(provider_str, debug=True)
                    else:
                        client = Client(provider_str)

                client_list.append(client)
            # If the FDSN service is down, then an FDSNException is raised
            except FDSNException:
                logging.warning('Unable to initalize client %s' % provider_str)
            except KeyError:
                logging.warning('Unable to initalize client %s' % provider_str)

        if len(client_list):
            # Pass off the initalized clients to the Mass Downloader
            if logging.getLevelName(root.level) == 'DEBUG':
                for handler in root.handlers:
                    if hasattr(handler, "baseFilename"):
                        log_file = getattr(handler, 'baseFilename')
                sys.stdout = open(log_file, 'a')
                mdl = MassDownloader(providers=client_list, debug=True)
            else:
                mdl = MassDownloader(providers=client_list)
            logging.info('Downloading new MiniSEED files...')
            # The data will be downloaded to the ``./waveforms/`` and
            # ``./stations/`` folders with automatically chosen file names.
            mdl.download(domain, restrictions, mseed_storage=rawdir,
                         stationxml_storage=rawdir)
            sys.stdout.close()

            if self.stream_collection:
                seed_files = glob.glob(os.path.join(rawdir, '*.mseed'))
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
                    streams=streams, drop_non_free=self.drop_non_free)
                return stream_collection
            else:
                return None
