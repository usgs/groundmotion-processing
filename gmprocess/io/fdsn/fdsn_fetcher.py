# stdlib imports
import tempfile
import os.path
import logging
import glob

# third party imports
import pytz
from obspy.core.utcdatetime import UTCDateTime
from obspy.core.stream import read
from obspy import read_inventory
from obspy.clients.fdsn.mass_downloader import (CircularDomain,
                                                Restrictions,
                                                MassDownloader)

# local imports
from gmprocess.io.fetcher import DataFetcher, _get_first_value
from gmprocess.io.fdsn.core import read_fdsn
from gmprocess.streamcollection import StreamCollection
from gmprocess.stationtrace import StationTrace
from gmprocess.stationstream import StationStream
from gmprocess.config import get_config


# default values for this fetcher
# if None specified in constructor, AND no parameters specified in
# config, then use these.
RADIUS = 4  # dd
TIME_BEFORE = 10  # seconds
TIME_AFTER = 420  # seconds
CHANNELS = ["HN[ZNE]"]  # default to only get strong motion stations

URL_ERROR_CODE = 200  # if we get this from a request, we're good

OBSPY_LOGGER = "obspy.clients.fdsn.mass_downloader"


class FDSNFetcher(DataFetcher):
    def __init__(self, time, lat, lon,
                 depth, magnitude,
                 radius=None, time_before=None,
                 time_after=None, channels=None,
                 rawdir=None, config=None, drop_non_free=True):
        """Create an FDSNFetcher instance.

        Download waveform data from the all available FDSN sites
        using the Obspy mass downloader functionality.

        Args:
            time (datetime): Origin time.
            lat (float): Origin latitude.
            lon (float): Origin longitude.
            depth (float): Origin depth.
            magnitude (float): Origin magnitude.
            radius (float): Search radius (km).
            time_before (float): Seconds before arrival time (sec).
            time_after (float): Seconds after arrival time (sec).
            rawdir (str): Path to location where raw data will be stored.
                          If not specified, raw data will be deleted.
            config (dict):
                Dictionary containing configuration. 
                If None, retrieve global config.
            drop_non_free (bool):
                Option to ignore non-free-field (borehole, sensors on structures, etc.)
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

        radius = _get_first_value(radius, cfg_radius, RADIUS)
        time_before = _get_first_value(time_before,
                                       cfg_time_before,
                                       TIME_BEFORE)
        time_after = _get_first_value(time_after,
                                      cfg_time_after,
                                      TIME_AFTER)
        channels = _get_first_value(channels, cfg_channels, CHANNELS)

        tz = pytz.UTC
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

        self.drop_non_free = drop_non_free
        self.BOUNDS = [-180, 180, -90, 90]

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

        restrictions = Restrictions(
            # Define the temporal bounds of the waveform data.
            starttime=origin_time - self.time_before,
            endtime=origin_time + self.time_after,

            reject_channels_with_gaps=True,
            # Any trace that is shorter than 95 % of the
            # desired total duration will be discarded.
            minimum_length=0.95,

            # No two stations should be closer than 10 km to each other.
            minimum_interstation_distance_in_m=10E3,

            channel_priorities=self.channels)

        # No specified providers will result in all known ones being queried.
        mdl = MassDownloader()

        # we can have a problem of file overlap, so let's remove existing
        # mseed files from the raw directory.
        logging.info('Deleting old MiniSEED files...')
        delete_old_files(rawdir, '*.mseed')

        # remove existing png files as well
        logging.info('Deleting old PNG files...')
        delete_old_files(rawdir, '*.png')

        # remove existing xml files as well
        logging.info('Deleting old XML files...')
        delete_old_files(rawdir, '*.xml')

        logging.info('Downloading new MiniSEED files...')
        # The data will be downloaded to the ``./waveforms/`` and ``./stations/``
        # folders with automatically chosen file names.
        mdl.download(domain, restrictions, mseed_storage=rawdir,
                     stationxml_storage=rawdir)

        seed_files = glob.glob(os.path.join(rawdir, '*.mseed'))
        streams = []
        for seed_file in seed_files:
            tstreams = read_fdsn(seed_file)
            streams += tstreams

        stream_collection = StreamCollection(streams=streams,
                                             drop_non_free=self.drop_non_free)
        return stream_collection


def delete_old_files(rawdir, pattern):
    pfiles = glob.glob(os.path.join(rawdir, pattern))
    for pfile in pfiles:
        os.remove(pfile)
