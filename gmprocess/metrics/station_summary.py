# stdlib imports
from collections import OrderedDict
import logging
import re

# third party imports
import numpy as np
from obspy.core.stream import Stream

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


class StationSummary(object):
    """
    Class for returning pgm values for specific components.
    """

    def __init__(self):
        self._station_code = None
        self._components = None
        self._imts = None
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
        station.components = np.sort(components)
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
            period_params = CONFIG['metrics']['periods']
            if period_params['use_array']:
                start = period_params['start']
                stop = period_params['stop']
                num = period_params['num']
                if period_params['spacing'] == 'logspace':
                    periods = np.logspace(start, stop, num)
                else:
                    periods = np.linspace(start, stop, num)
                additional_periods = [p for p in period_params['additional_periods']]
                periods = set(np.append(periods, additional_periods))
        else:
            periods, imts = station.get_periods(set(np.sort(imts)))
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

        station.station_code = stream[0].stats['station']
        station.stream = stream
        # Get oscillators
        rot = False
        for component in components:
            if component.upper().startswith('ROTD'):
                rot = True
        station.generate_oscillators(imts, periods, damping, rot)
        # Gather pgm/imt for each
        station.pgms = station.gather_pgms(components, periods, smoothing,
                bandwidth)
        return station

    def gather_pgms(self, components, periods, smoothing, bandwidth):
        """
        Gather pgms by getting components for each imt.

        Returns:
            dictionary: Dictionary of pgms.

        Notes:
            Assumes generate_oscillators has already been called for
            this class instance.
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
                            smoothing, bandwidth)
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

    def generate_oscillators(self, imts, periods, damping, rotate=False):
        """
        Create dictionary of requested imt and its coinciding oscillators.

        Returns:
            dictionary: dictionary of oscillators for each imt.
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
                oscillator = get_acceleration(stream)
                oscillator_dict['FAS'] = oscillator
            elif imt.upper().startswith('SA'):
                for period in periods:
                    tag = 'SA(' + str(period) + ')'
                    oscillator = get_spectral(
                        period, stream,
                        damping=damping)
                    oscillator_dict[tag] = oscillator
                    if rotate:
                        oscillator = get_spectral(
                            period, stream,
                            damping=damping, rotation='nongm')
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
                for period in periods:
                    imts += ['FAS(' + str(period) + ')']
            elif key.find('ROT') < 0:
                imts += [key]

        self.imts = imts
        self.oscillators = oscillator_dict

    def get_periods(self, imts):
        periods = []
        stripped_imts = []
        for imt in imts:
            if imt.upper().startswith('SA'):
                try:
                    periods += [float(re.search('\d+\.*\d*', imt).group())]
                    if 'SA' not in stripped_imts:
                        stripped_imts += ['SA']
                except Exception:
                    fmt = "Invalid period for imt: %r. Skipping..."
                    logging.warning(fmt % (imt))
            if imt.upper().startswith('FAS'):
                try:
                    periods += [float(re.search('\d+\.*\d*', imt).group())]
                    if 'FAS' not in stripped_imts:
                        stripped_imts += ['FAS']
                except Exception:
                    fmt = "Invalid period for imt: %r. Skipping..."
                    logging.warning(fmt % (imt))
            else:
                stripped_imts += [imt.upper()]
        return periods, stripped_imts



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
