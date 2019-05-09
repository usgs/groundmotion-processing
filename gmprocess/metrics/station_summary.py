# stdlib imports
from collections import OrderedDict
import logging
import re

# third party imports
from lxml import etree
import numpy as np
from obspy.core.stream import Stream
from obspy.geodetics.base import gps2dist_azimuth
from openquake.hazardlib.geo.geodetic import distance
import pandas as pd

# local imports
from gmprocess.config import get_config
from gmprocess.metrics.gather import gather_pgms
from gmprocess.metrics.metrics_controller import MetricsController


XML_UNITS = {'pga': '%g',
             'pgv': 'cm/s',
             'sa': '%g',
             'arias': 'm/s',
             'fas': 'cm/s'}


class StationSummary(object):
    """
    Class for returning pgm values for specific components.
    """

    def __init__(self):
        self._bandwidth = None
        self._components = None
        self._coordinates = None
        self._damping = None
        self._elevation = None
        self._epicentral_distance = None
        self._hypocentral_distance = None
        self._imts = None
        self._origin = None
        self._pgms = None
        self._smoothing = None
        self._starttime = None
        self._station_code = None
        self._stream = None
        self._summary = None

    @property
    def available_imcs(self):
        """
        Helper method for getting a list of components.

        Returns:
            list: List of available components (str).
        """
        return [x for x in gather_pgms()[1]]

    @property
    def available_imts(self):
        """
        Helper method for getting a list of measurement types.

        Returns:
            list: List of available measurement types (str).
        """
        return [x for x in gather_pgms()[0]]

    @property
    def bandwidth(self):
        """
        Helper method for getting the defined bandwidth.

        Returns:
            float: Bandwidth used in smoothing.
        """
        return self._bandwidth

    @property
    def components(self):
        """
        Helper method returning a list of requested/calculated components.

        Returns:
            list: List of requested/calculated components (str).
        """
        return list(self._components)

    @property
    def coordinates(self):
        """
        Helper method returning the coordinates of the station.

        Returns:
            list: List of coordinates (str).
        """
        return self._coordinates

    @property
    def damping(self):
        """
        Helper method for getting the damping used in the spectral amplitude
        calculation.

        Returns:
            float: Damping used in SA calculation.
        """
        return self._damping

    @property
    def elevation(self):
        """
        Helper method for getting the station elevation.

        Returns:
            float: Station elevation
        """
        return self._elevation

    @property
    def epicentral_distance(self):
        """
        Helper method for getting the epicentral distance.

        Returns:
            float: Epicentral distance.
        """
        return self._epicentral_distance

    @classmethod
    def from_config(cls, stream, config=None, origin=None):
        """
        Args:
            stream (obspy.core.stream.Stream): Strong motion timeseries
                for one station.
            origin (obspy.core.event.origin.Origin):
                Origin for the event containing latitude, longitude, and
                depth.
            config (dictionary): Configuration dictionary.

        Note:
            Assumes a processed stream with units of gal (1 cm/s^2).
            No processing is done by this class.
        """
        if config is None:
            config = get_config()
        station = cls()

        damping = config['metrics']['sa']['damping']
        smoothing = config['metrics']['fas']['smoothing']
        bandwidth = config['metrics']['fas']['bandwidth']

        station._damping = damping
        station._smoothing = smoothing
        station._bandwidth = bandwidth
        station._stream = stream
        station.origin = origin
        station.set_metadata()
        metrics = MetricsController.from_config(stream, config=config,
                origin=origin)
        pgms = metrics.pgms
        if pgms is None:
            station._components = metrics.imcs
            station._imts = metrics.imts
            station.pgms = pd.DataFrame.from_dict({
                'IMT': [],
                'IMC': [],
                'Result': []
            })
        else:
            station._components = set(pgms['IMC'].tolist())
            station._imts = set(pgms['IMT'].tolist())
            station.pgms = pgms
        station._summary = station.get_summary()
        return station

    @classmethod
    def from_pgms(cls, station_code, pgms):
        """
        Args:
            station_code (str): Station code for the given pgms.
            pgms (dictionary): Dictionary of pgms.

        Note:
            The pgm dictionary must be formated as imts with subdictionaries
            containing imcs:
                {
                  'SA1.0': {
                    'H2': 84.23215974982956,
                    'H1': 135.9267934939141,
                    'GREATER_OF_TWO_HORIZONTALS': 135.9267934939141,
                    'Z': 27.436966897028416
                  },
                  ...
                }
            This should be the default format for significant ground motion
            parametric data from COMCAT.
        """
        station = cls()
        station._station_code = station_code
        dfdict = {'IMT': [], 'IMC': [], 'Result': []}
        for imt in pgms:
            for imc in pgms[imt]:
                dfdict['IMT'] += [imt]
                dfdict['IMC'] += [imc]
                dfdict['Result'] += [pgms[imt][imc]]
        pgmdf = pd.DataFrame.from_dict(dfdict)
        station.pgms = pgmdf
        imts = [key for key in pgms]
        components = []
        for imt in pgms:
            components += [imc for imc in pgms[imt]]
        station._components = np.sort(np.unique(components))
        station._imts = np.sort(imts)
        # stream should be set later with corrected a corrected stream
        # this stream (in units of gal or 1 cm/s^2) can be used to
        # calculate and set oscillators
        return station

    @classmethod
    def from_stream(cls, stream, components, imts, origin=None,
                    damping=None, smoothing=None, bandwidth=None, config=None):
        """
        Args:
            stream (obspy.core.stream.Stream): Strong motion timeseries
                for one station.
            components (list): List of requested components (str).
            imts (list): List of requested imts (str).
            origin (obspy.core.event.origin.Origin):
                Origin for the event containing latitude, longitude, and
                depth.
            damping (float): Damping of oscillator. Default is None.
            smoothing (float): Smoothing method. Default is None.
            bandwidth (float): Bandwidth of smoothing. Default is None.
            config (dictionary): Configuration dictionary.

        Note:
            Assumes a processed stream with units of gal (1 cm/s^2).
            No processing is done by this class.
        """
        if config is None:
            config = get_config()
        station = cls()
        imts = np.sort(imts)
        components = np.sort(components)

        if damping is None:
            damping = config['metrics']['sa']['damping']
        if smoothing is None:
            smoothing = config['metrics']['fas']['smoothing']
        if bandwidth is None:
            bandwidth = config['metrics']['fas']['bandwidth']

        station._damping = damping
        station._smoothing = smoothing
        station._bandwidth = bandwidth
        station._stream = stream
        station.origin = origin
        station.set_metadata()
        metrics = MetricsController(imts, components, stream,
                bandwidth=bandwidth, damping=damping, origin=origin,
                smooth_type=smoothing)
        pgms = metrics.pgms
        if pgms is None:
            station._components = metrics.imcs
            station._imts = metrics.imts
            station.pgms = pd.DataFrame.from_dict({
                'IMT': [],
                'IMC': [],
                'Result': []
            })
        else:
            station._components = set(pgms['IMC'].tolist())
            station._imts = set(pgms['IMT'].tolist())
            station.pgms = pgms
        station._summary = station.get_summary()
        return station

    def get_pgm(self, imt, imc):
        """
        Finds the imt/imc value requested.

        Returns:
            float: Value for the imt, imc requested.
        """
        imt = imt.upper()
        imc = imc.upper()
        if imt not in self.imts or imc not in self.components:
            return np.nan
        else:
            imt_df = self.pgms.loc[self.pgms.IMT == imt]
            imc_df = imt_df.loc[imt_df.IMC == imc]
            value = imc_df['Result'].tolist()[0]
            return value

    def get_summary(self):
        columns = ['STATION', 'NAME', 'SOURCE', 'NETID', 'LAT', 'LON', 'ELEVATION']
        if self.epicentral_distance is not None:
            columns += ['EPICENTRAL_DISTANCE']
        if self.hypocentral_distance is not None:
            columns += ['HYPOCENTRAL_DISTANCE']
        # set meta_data
        row = np.zeros(len(columns), dtype=list)
        row[0] = self.station_code
        name_str = self.stream[0].stats['standard']['station_name']
        row[1] = name_str
        source = self.stream[0].stats.standard['source']
        row[2] = source
        row[3] = self.stream[0].stats['network']
        row[4] = self.coordinates[0]
        row[5] = self.coordinates[1]
        row[6] = self.elevation
        if self.epicentral_distance is not None:
            row[7] = self.epicentral_distance
            if self.hypocentral_distance is not None:
                row[8] = self.hypocentral_distance
        elif self.hypocentral_distance is not None:
            row[7] = self.hypocentral_distance
        imcs = self.components
        imts = self.imts
        pgms = self.pgms
        meta_columns = pd.MultiIndex.from_product([columns, ['']])
        meta_dataframe = pd.DataFrame(np.array([row]), columns=meta_columns)
        pgm_columns = pd.MultiIndex.from_product([imcs, imts])
        pgm_data = np.zeros((1, len(imts) * len(imcs)))
        subindex = 0
        for imc in imcs:
            for imt in imts:
                dfidx = (pgms.IMT == imt) & (pgms.IMC == imc)
                result = pgms[dfidx].Result.tolist()
                if len(result) == 0:
                    value = np.nan
                else:
                    value = result[0]
                pgm_data[0][subindex] = value
                subindex += 1
        pgm_dataframe = pd.DataFrame(pgm_data, columns=pgm_columns)
        dataframe = pd.concat([meta_dataframe, pgm_dataframe], axis=1)
        return dataframe


    @property
    def hypocentral_distance(self):
        """
        Helper method for getting the hypocentral distance.

        Returns:
            float: Hypocentral distance.
        """
        return self._hypocentral_distance

    @property
    def imts(self):
        """
        Helper method returning a list of requested/calculated measurement
        types.

        Returns:
            list: List of requested/calculated measurement types (str).
        """
        return list(self._imts)

    @property
    def pgms(self):
        """
        Helper method returning a station's pgms.

        Returns:
            dictionary: Pgms for each imt and imc.
        """
        return self._pgms

    @pgms.setter
    def pgms(self, pgms):
        """
        Helper method to set the pgms attribute.

        Args:
            pgms (list): Dictionary of pgms for each imt and imc.
        """
        self._pgms = pgms

    def set_metadata(self):
        """
        Set the metadata for the station
        """
        stats = self.stream[0].stats
        self._starttime = stats.starttime
        self._station_code = stats.station
        if 'coordinates' not in stats:
            self._elevation = np.nan
            self._coordinates = (np.nan, np.nan)
            return
        lat = stats.coordinates.latitude
        lon = stats.coordinates.longitude
        if 'elevation' not in stats.coordinates or np.isnan(stats.coordinates.elevation):
            elev = 0
        else:
            elev = stats.coordinates.elevation
        self._elevation = elev
        self._coordinates = (lat, lon)
        if self.origin is not None:
            origin = self.origin
            dist, _, _ = gps2dist_azimuth(lat, lon,
                     origin.latitude, origin.longitude)
            self._epicentral_distance = dist/1000
            if origin.depth is not None:
                self._hypocentral_distance = distance(lat, lon, elev/1000,
                        origin.latitude, origin.longitude, origin.depth/1000)

    @property
    def smoothing(self):
        """
        Helper method for getting the defined smoothing used for the
        calculation FAS.

        Returns:
            string: Smoothing method used.
        """
        return self._smoothing

    @property
    def starttime(self):
        """
        Helper method returning a station's starttime.

        Returns:
            str: Start time for one station.
        """
        return self._starttime

    @property
    def station_code(self):
        """
        Helper method returning a station's station code.

        Returns:
            str: Station code for one station.
        """
        return self._station_code

    @property
    def stream(self):
        """
        Helper method returning a station's stream.

        Returns:
            obspy.core.stream.Stream: Stream for one station.
        """
        return self._stream

    @stream.setter
    def stream(self, stream):
        """
        Helper method to set the stream attribute.

        Args:
            stream (obspy.core.stream.Stream): Stream for one station.
        """
        if self.stream is not None:
            logging.warning(
                'Setting failed: the stream object cannot be '
                'changed. A new instance of StationSummary must be created.')
        else:
            if not isinstance(stream, Stream):
                logging.warning('Setting failed: not a stream object.')
            elif (stream[0].stats['station'].upper() !=
                  self.station_code.upper()):
                logging.warning(
                    'Setting failed: stream station does not match '
                    'StationSummary.station_code.')
            else:
                self._stream = stream

    @property
    def summary(self):
        """
        Helper method returning a station's summary.

        Returns:
            pandas.Dataframe: Summary for one station.
        """
        return self._summary

    @classmethod
    def fromMetricXML(cls, xmlstr):
        imtlist = gather_pgms()[0]
        root = etree.fromstring(xmlstr)
        pgms = {}
        station_code = None
        damping = None
        for element in root.iter():
            etag = element.tag
            if etag == 'waveform_metrics':
                station_code = element.attrib['station_code']
                continue
            elif etag in imtlist:
                tdict = {}
                if etag in ['sa', 'fas']:
                    period = element.attrib['period']
                    if 'damping' in element.attrib:
                        damping = float(element.attrib['damping'])
                    imt = '%s(%s)' % (etag.upper(), period)
                else:
                    imt = etag.upper()
                for imc_element in element.getchildren():
                    imc = imc_element.tag.upper()
                    value = float(imc_element.text)
                    tdict[imc] = value

                pgms[imt] = tdict
        station = cls.from_pgms(station_code, pgms)
        station._damping = damping
        return station

    def getMetricXML(self):
        """Return XML for waveform metrics as defined for our ASDF implementation.

        Returns:
            str: XML in the form:
                <waveform_metrics>
                    <rot_d50>
                        <pga units="m/s**2">0.45</pga>
                        <sa percent_damping="5.0" units="g">
                        <value period="2.0">0.2</value>
                    </rot_d50>
                    <maximum_component>
                    </maximum_component>
                </waveform_metrics>

        """
        FLOAT_MATCH = r'[0-9]*\.[0-9]*'
        root = etree.Element('waveform_metrics',
                             station_code=self.station_code)
        for imt in self.imts:
            imtstr = imt.lower()
            units = None
            if imtstr in XML_UNITS:
                units = XML_UNITS[imtstr]
            else:
                for key in XML_UNITS.keys():
                    if imtstr.startswith(key):
                        units = XML_UNITS[key]
                        break
            if units is None:
                raise KeyError('Could not find units for IMT %s' % imtstr)

            period = None
            if imtstr.startswith('sa') or imtstr.startswith('fas'):
                period = float(re.search(FLOAT_MATCH, imtstr).group())
                attdict = {'period': '%.1f' % period,
                           'units': units}
                if imtstr.startswith('sa'):
                    imtstr = 'sa'
                    attdict['damping'] = '%.2f' % self._damping
                else:
                    imtstr = 'fas'
                imt_tag = etree.SubElement(root, imtstr, attrib=attdict)
            else:
                imt_tag = etree.SubElement(root, imtstr, units=units)

            for imc in self.components:
                imcstr = imc.lower().replace('(','').replace(')','')
                imc_tag = etree.SubElement(imt_tag, imcstr)
                idx = (self.pgms.IMT == imt) & (self.pgms.IMC == imc)
                vals = self.pgms[idx].Result.tolist()
                if len(vals) == 0:
                    value = np.nan
                else:
                    value = vals[0]
                imc_tag.text = '%.4f' % value
        xmlstr = etree.tostring(root, pretty_print=True,
                                encoding='utf-8', xml_declaration=True)
        return xmlstr

    def toSeries(self):
        """Render StationSummary as a Pandas Series object.

        Returns:
            Series:
                Multi-Indexed Pandas Series where IMTs are top-level indices and
                components are sub-indices.
        """
        imts = self.imts
        imcs = self.components
        index = pd.MultiIndex.from_product([imts, imcs])
        data = []
        for imt in imts:
            for imc in imcs:
                idx = (self.pgms.IMT == imt) & (self.pgms.IMC == imc)
                vals = self.pgms[idx].Result.tolist()
                if len(vals) == 0:
                    value = np.nan
                else:
                    value = vals[0]
                data.append(value)
        series = pd.Series(data, index)
        return series
