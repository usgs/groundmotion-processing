# stdlib imports
from collections import OrderedDict
import logging
import re

# third party imports
import numpy as np
from obspy.core.stream import Stream
from lxml import etree
import pandas as pd

# local imports
from gmprocess.config import get_config
from gmprocess.metrics.imt.arias import calculate_arias
from gmprocess.metrics.imt.pga import calculate_pga
from gmprocess.metrics.imt.pgv import calculate_pgv
from gmprocess.metrics.imt.sa import calculate_sa
from gmprocess.metrics.imt.fas import calculate_fas
from gmprocess.metrics.gather import get_pgm_classes
from gmprocess.metrics.oscillators import (
    get_acceleration, get_spectral, get_velocity)


CONFIG = get_config()

XML_UNITS = {'pga': '%g',
             'pgv': 'cm/s',
             'sa': '%g',
             'arias': 'cm/s',
             'fas': 'cm/s'}


class StationSummary(object):
    """
    Class for returning pgm values for specific components.
    """

    def __init__(self):
        self._bandwidth = None
        self._components = None
        self._damping = None
        self._imts = None
        self._smoothing = None
        self._station_code = None
        self._stream = None
        self._oscillators = None
        self._pgms = None

    @property
    def available_imcs(self):
        """
        Helper method for getting a list of components.

        Returns:
            list: List of available components (str).
        """
        return [key for key in get_pgm_classes('imc')]

    @property
    def available_imts(self):
        """
        Helper method for getting a list of measurement types.

        Returns:
            list: List of available measurement types (str).
        """
        return [key for key in get_pgm_classes('imt')]

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
        return self._components

    @components.setter
    def components(self, components):
        """
        Helper method to set the components attribute.

        Args:
            components (list): List of components (str).
        """
        self._components = list(components)

    @property
    def damping(self):
        """
        Helper method for getting the damping used in the spectral amplitude
        calculation.

        Returns:
            float: Damping used in SA calculation.
        """
        return self._damping

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
        station.station_code = station_code
        station.pgms = pgms
        imts = [key for key in pgms]
        components = []
        for imt in pgms:
            components += [imc for imc in pgms[imt]]
        station.components = np.sort(np.unique(components))
        station.imts = np.sort(imts)
        # stream should be set later with corrected a corrected stream
        # this stream (in units of gal or 1 cm/s^2) can be used to
        # calculate and set oscillators
        return station

    @classmethod
    def from_stream(cls, stream, components=None, imts=None, damping=None,
                    smoothing=None, bandwidth=None):
        """
        Args:
            stream (obspy.core.stream.Stream): Strong motion timeseries
                for one station.
            components (list): List of requested components (str).
            imts (list): List of requested imts (str).
            damping (float): Damping of oscillator. Default is 5% (0.05)

        Note:
            Assumes a processed stream with units of gal (1 cm/s^2).
            No processing is done by this class.
        """
        station = cls()
        if imts is None:
            imts = set(np.sort(CONFIG['metrics']['output_imts']))
            sa_period_params = CONFIG['metrics']['sa']['periods']
            fas_period_params = CONFIG['metrics']['fas']['periods']
            period_sets = []
            for period_params in [sa_period_params, fas_period_params]:
                if period_params['use_array']:
                    start = period_params['start']
                    stop = period_params['stop']
                    num = period_params['num']
                    if period_params['spacing'] == 'logspace':
                        periods = np.logspace(start, stop, num)
                    else:
                        periods = np.linspace(start, stop, num)
                    additional_periods = [
                        p for p in period_params['defined_periods']]
                    periods = set(np.append(periods, additional_periods))
                else:
                    periods = set(
                        [p for p in period_params['defined_periods']])
                period_sets += [periods]
            sa_periods, fas_periods = period_sets[0], period_sets[1]
        else:
            period_dict = station.parse_periods(set(np.sort(imts)))
            imts = period_dict['imts']
            sa_periods = period_dict['sa_periods']
            fas_periods = period_dict['fas_periods']
        if components is None:
            components = set(np.sort(CONFIG['metrics']['output_imcs']))
        else:
            components = set(np.sort(components))

        if damping is None:
            damping = CONFIG['metrics']['sa']['damping']
        if smoothing is None:
            smoothing = CONFIG['metrics']['fas']['smoothing']
        if bandwidth is None:
            bandwidth = CONFIG['metrics']['fas']['bandwidth']

        station._damping = damping
        station._smoothing = smoothing
        station._bandwidth = bandwidth
        station.station_code = stream[0].stats['station']
        station.stream = stream
        # Get oscillators
        rot = False
        for component in components:
            if component.upper().startswith('ROTD'):
                rot = True
        station.generate_oscillators(imts, sa_periods, fas_periods, rot)
        # Gather pgm/imt for each
        station.pgms = station.gather_pgms(components, fas_periods)
        return station

    def gather_pgms(self, components, periods):
        """
        Gather pgms by getting components for each imt.

        Args:
            components (list): List of imcs.
            periods (list): List of periods for the calculate_fas method.

        Returns:
            dictionary: Dictionary of pgms.

        Notes:
            Assumes generate_oscillators has already been called for
            this class instance. Smoothing and bandwidth parameters must be set.
        """
        pgm_dict = {}
        for oscillator in self.oscillators:
            if oscillator.find('ROT') < 0:
                stream = self.oscillators[oscillator]
                if oscillator == 'PGA':
                    pga = calculate_pga(stream, components)
                    pgm_dict[oscillator] = pga
                elif oscillator == 'PGV':
                    pgv = calculate_pgv(stream, components)
                    pgm_dict[oscillator] = pgv
                elif oscillator.startswith('SA'):
                    if oscillator + '_ROT' in self.oscillators:
                        rotation_matrix = self.oscillators[oscillator + '_ROT']
                        sa = calculate_sa(stream, components, rotation_matrix)
                    else:
                        sa = calculate_sa(stream, components)
                    pgm_dict[oscillator] = sa
                elif oscillator.startswith('FAS'):
                    fas = calculate_fas(stream, components, periods,
                                        self.smoothing, self.bandwidth)
                    for period in fas:
                        tag = 'FAS(' + str(period) + ')'
                        pgm_dict[tag] = {}
                        pgm_dict[tag]['GEOMETRIC_MEAN'] = fas[period]
                elif oscillator.startswith('ARIAS'):
                    arias = calculate_arias(stream, components)
                    pgm_dict[oscillator] = arias
        components = []
        for imt in pgm_dict:
            components += [imc for imc in pgm_dict[imt]]
        self.components = set(components)
        return pgm_dict

    def generate_oscillators(self, imts, sa_periods, fas_periods, rotate=False):
        """
        Create dictionary of requested imt and its coinciding oscillators.

        Args:
            imts (list): List of imts.
            sa_periods (list): List of periods. Used to generate the SA
                    oscillators.
            fas_periods (list): List of periods. Used to generate the FAS
                    oscillators.
            rotate (bool): Whether to rotate the sa oscillators for the ROTD
                    component.

        Returns:
            dictionary: dictionary of oscillators for each imt.

        Notes:
            Damping value must be set.
        """
        if self.stream is None:
            raise Exception('StationSummary.stream is not set.')
        oscillator_dict = OrderedDict()
        for imt in imts:
            stream = self.stream.copy()
            if imt.upper() == 'PGA':
                oscillator = get_acceleration(stream)
                oscillator_dict['PGA'] = oscillator
            elif imt.upper() == 'PGV':
                oscillator = get_velocity(stream)
                oscillator_dict['PGV'] = oscillator
            elif imt.upper() == 'FAS':
                oscillator = get_acceleration(stream, 'cm/s/s')
                oscillator_dict['FAS'] = oscillator
            elif imt.upper().startswith('SA'):
                for period in sa_periods:
                    tag = 'SA(' + str(period) + ')'
                    oscillator = get_spectral(
                        period, stream,
                        damping=self.damping)
                    oscillator_dict[tag] = oscillator
                    if rotate:
                        oscillator = get_spectral(
                            period, stream,
                            damping=self.damping, rotation='nongm')
                        oscillator_dict[tag + '_ROT'] = oscillator
            elif imt.upper() == 'ARIAS':
                oscillator = get_acceleration(stream, units='m/s/s')
                oscillator_dict['ARIAS'] = oscillator
            else:
                fmt = "Invalid imt: %r. Skipping..."
                logging.warning(fmt % (imt))
        imts = []
        for key in oscillator_dict:
            if key == 'FAS':
                for period in fas_periods:
                    imts += ['FAS(' + str(period) + ')']
            elif key.find('ROT') < 0:
                imts += [key]

        self.imts = imts
        self.oscillators = oscillator_dict

    def get_pgm(self, imt, imc):
        """
        Get a value for a requested imt and imc from pgms dictionary.

        Args:
            imt (str): Intensity measurement type.
            imc (str): Intensity measurement component.

        Returns:
            float: Peak ground motion value.
        """
        if self.pgms is None:
            raise Exception('No pgms have been calculated.')
        imt = imt.upper()
        imc = imc.upper()
        return self.pgms[imt][imc]

    @property
    def imts(self):
        """
        Helper method returning a list of requested/calculated measurement
        types.

        Returns:
            list: List of requested/calculated measurement types (str).
        """
        return self._imts

    @imts.setter
    def imts(self, imts):
        """
        Helper method to set the imts attribute.

        Args:
            imts (list): List of imts (str).
        """
        self._imts = list(imts)

    @property
    def oscillators(self):
        """
        Helper method returning a station's oscillators.

        Returns:
            dictionary: Stream for each imt.
        """
        return self._oscillators

    @oscillators.setter
    def oscillators(self, oscillators):
        """
        Helper method to set the oscillators attribute.

        Args:
            oscillators (dictionary): Stream for each imt.
        """
        self._oscillators = oscillators

    def parse_periods(self, imts):
        """
        Parse the periods for the FAS and SA imts.

        Args:
            imts (list): List of imts.

        Returns:
            dictionary: Defines the stripped imts (period is now removed from
                    the string), the sa periods, and fas periods.
        """
        sa_periods = []
        fas_periods = []
        stripped_imts = []
        for imt in imts:
            if imt.upper().startswith('SA'):
                try:
                    period = float(re.search('\d+\.*\d*', imt).group())
                    if period not in sa_periods:
                        sa_periods += [period]
                    if 'SA' not in stripped_imts:
                        stripped_imts += ['SA']
                except Exception:
                    fmt = "Invalid period for imt: %r. Skipping..."
                    logging.warning(fmt % (imt))
            elif imt.upper().startswith('FAS'):
                try:
                    period = float(re.search('\d+\.*\d*', imt).group())
                    if period not in fas_periods:
                        fas_periods += [period]
                    if 'FAS' not in stripped_imts:
                        stripped_imts += ['FAS']
                except Exception:
                    fmt = "Invalid period for imt: %r. Skipping..."
                    logging.warning(fmt % (imt))
            else:
                stripped_imts += [imt.upper()]
        period_dict = {'imts': stripped_imts, 'sa_periods': sa_periods,
                       'fas_periods': fas_periods}
        return period_dict

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
    def station_code(self):
        """
        Helper method returning a station's station code.

        Returns:
            str: Station code for one station.
        """
        return self._station_code

    @station_code.setter
    def station_code(self, station_code):
        """
        Helper method to set the station code attribute.

        Args:
            station_code (str): Station code for one station.
        """
        if self.station_code is not None:
            logging.warning(
                'Setting failed: the station code cannot be '
                'changed. A new instance of StationSummary must be created.')
        else:
            self._station_code = station_code

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

    @classmethod
    def fromMetricXML(cls, xmlstr):
        imtlist = ['pga', 'pgv', 'sa', 'fas', 'arias']
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
        for imt, imcdict in self.pgms.items():
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

            for imc, value in imcdict.items():
                imcstr = imc.lower()
                imc_tag = etree.SubElement(imt_tag, imcstr)
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
            imt_dict = self.pgms[imt]
            for imc in imcs:
                if imc not in imt_dict:
                    data.append(np.nan)
                else:
                    data.append(imt_dict[imc])
        series = pd.Series(data, index)
        return series
