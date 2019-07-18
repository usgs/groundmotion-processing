# Std library imports
from collections import OrderedDict
import importlib
import inspect
import logging
import re

# Third party imports
import numpy as np
import pandas as pd

# Local imports
from gmprocess.config import get_config
from gmprocess.constants import GAL_TO_PCTG
from gmprocess.metrics.exception import PGMException
from gmprocess.metrics.gather import gather_pgms
from gmprocess.stationstream import StationStream


class MetricsController(object):
    """
    Class for compiling metrics.
    """

    def __init__(self, imts, imcs, timeseries, bandwidth=None, damping=None,
                 event=None, smooth_type=None):
        """
        Args:
            imts (list):
                Intensity measurement types (string) to calculate.
            imcs (list):
                Intensity measurement components (string) to
                calculate. timeseries (StationStream): Stream of the
                timeseries data.
            event (ScalarEvent):
                Defines the focal time, geographic location, and magnitude of
                an earthquake hypocenter. Default is None.
            damping (float):
                Damping for the oscillator calculation.
            bandwidth (float):
                Bandwidth for the smoothing calculation.
            smoothing (string):
                Currently not used, as konno_ohmachi is the only smoothing
                type.
        """
        if not isinstance(imts, (list, np.ndarray)):
            imts = [imts]
        if not isinstance(imcs, (list, np.ndarray)):
            imcs = [imcs]
        self.imts = set(np.sort([imt.lower() for imt in imts]))
        self.imcs = set(np.sort([imc.lower() for imc in imcs]))
        if 'radial_transverse' in self.imcs and event is None:
            raise PGMException('MetricsController: Event is required for '
                               'radial_transverse imc')
        self.timeseries = timeseries
        self.validate_stream()
        self.event = event
        self.config = get_config()
        self.damping = damping
        self.smooth_type = smooth_type
        self.bandwidth = bandwidth
        if damping is None:
            self.damping = self.config['metrics']['sa']['damping']
        if smooth_type is None:
            self.smooth_type = self.config['metrics']['fas']['smoothing']
        if bandwidth is None:
            self.bandwidth = self.config['metrics']['fas']['bandwidth']
        self._available_imts, self._available_imcs = gather_pgms()
        self._step_sets = self.get_steps()
        imtstr = '_'.join(imts)
        if '_sa' in imtstr or imtstr.startswith('sa'):
            self._times = self._get_horizontal_time()
        else:
            self._times = None
        self.pgms = self.execute_steps()

    @classmethod
    def from_config(cls, timeseries, config=None, event=None):
        """
        Create class instance from a config. Can be a custom config or the
        default config found in ~/.gmprocess/config.yml.

        Args:
            timeseries (StationStream):
                Stream of the timeseries data.
            config (dictionary):
                Custom config. Default is None, and the default config will
                be used.
            event (ScalarEvent):
                Defines the focal time, geographic location and magnitude of
                an earthquake hypocenter. Default is None.

        Notes:
            Custom configs must be in the following format:
                    {'metrics':
                            'output_imcs': <list>,
                            'output_imts': <list>,
                            'sa':{
                                    'damping': <float>,
                                    'periods': {
                                            'start': <float>,
                                            'stop': <float>,
                                            'num': <float>,
                                            'spacing': <string>,
                                            'use_array': <bool>,
                                            'defined_periods': <list>,
                                    }
                            },
                            'fas':{
                                    'smoothing': <float>,
                                    'bandwidth': <float>,
                                    'periods': {
                                            'start': <float>,
                                            'stop': <float>,
                                            'num': <float>,
                                            'spacing': <string>,
                                            'use_array': <bool>,
                                            'defined_periods': <list>,
                                    }
                            }
                    }
            Currently the only acceptied smoothing type is 'konno_ohmachi',
            and the options for spacing are 'linspace' or 'logspace'.
        """
        if config is None:
            config = get_config()
        metrics = config['metrics']
        config_imts = [imt.lower() for imt in metrics['output_imts']]
        imcs = [imc.lower() for imc in metrics['output_imcs']]
        # append periods
        imts = []
        for imt in config_imts:
            if imt == 'sa':
                if metrics['sa']['periods']['use_array']:
                    start = metrics['sa']['periods']['start']
                    stop = metrics['sa']['periods']['stop']
                    num = metrics['sa']['periods']['num']
                    if metrics['sa']['periods']['spacing'] == 'logspace':
                        periods = np.logspace(start, stop, num=num)
                    else:
                        periods = np.linspace(start, stop, num=num)
                    for period in periods:
                        imts += ['sa' + str(period)]
                else:
                    for period in metrics['sa']['periods']['defined_periods']:
                        imts += ['sa' + str(period)]
            elif imt == 'fas':
                if metrics['fas']['periods']['use_array']:
                    start = metrics['fas']['periods']['start']
                    stop = metrics['fas']['periods']['stop']
                    num = metrics['fas']['periods']['num']
                    if metrics['fas']['periods']['spacing'] == 'logspace':
                        periods = np.logspace(start, stop, num=num)
                    else:
                        periods = np.linspace(start, stop, num=num)
                    for period in periods:
                        imts += ['fas' + str(period)]
                else:
                    for period in metrics['fas']['periods']['defined_periods']:
                        imts += ['fas' + str(period)]
            else:
                imts += [imt]
        damping = metrics['sa']['damping']
        smoothing = metrics['fas']['smoothing']
        bandwidth = metrics['fas']['bandwidth']
        controller = cls(imts, imcs, timeseries, bandwidth=bandwidth,
                         damping=damping, event=event, smooth_type=smoothing)
        
        return controller

    @property
    def step_sets(self):
        """
        Dictionary of steps for each imt/imc pair.

        Returns:
            dictionary: Defines a set of steps for each imt/imc pair.
        """
        return self._step_sets

    def get_steps(self):
        """
        Sets up the step_sets dictionary.

        Returns:
            dictionary: Defines a set of steps for each imt/imc pair.

        Notes:
            Invalid imcs and imts will not be added to the dictionary.
        """
        pgm_steps = {}
        for imt in self.imts:
            period = None
            integrate = False
            differentiate = False
            baseimt = imt
            # Determine whether an integration/differentiation step is
            # necessary
            if (imt == 'pgv' and
                    self.timeseries[0].stats.standard.units == 'acc'):
                integrate = True
            elif (imt != 'pgv' and
                  self.timeseries[0].stats.standard.units == 'vel'):
                differentiate = True
            # SA and FAS imts include a period which must be parsed from
            # the imt string
            if imt.startswith('sa'):
                period = self._parse_period(imt)
                if period is None:
                    continue
                imt = 'sa'
            elif imt.startswith('fas'):
                period = self._parse_period(imt)
                if period is None:
                    continue
                imt = 'fas'
            if imt not in self._available_imts:
                continue
            for imc in self.imcs:
                percentile = None
                baseimc = imc
                # ROTD and GMROTD imcs include a period which must be parsed
                # from the imc string
                if 'rot' in imc:
                    percentile = self._parse_percentile(imc)
                    if imc.startswith('gm'):
                        imc = 'gmrotd'
                    else:
                        imc = 'rotd'
                if imc not in self._available_imcs:
                    continue
                # Import
                imt_path = 'gmprocess.metrics.imt.'
                imc_path = 'gmprocess.metrics.imc.'
                imt_mod = importlib.import_module(imt_path + imt)
                imc_mod = importlib.import_module(imc_path + imc)
                imt_class = self._get_subclass(
                    inspect.getmembers(imt_mod, inspect.isclass), 'IMT')
                imc_class = self._get_subclass(
                    inspect.getmembers(imc_mod, inspect.isclass), 'IMC')
                imt_class_instance = imt_class(imt, imc, period)
                if not imt_class_instance.valid_combination(imc):
                    continue
                imc_class_instance = imc_class(imc, imt, percentile)
                # Get Steps
                steps = OrderedDict()
                if differentiate:
                    steps['Transform1'] = 'differentiate'
                elif integrate:
                    steps['Transform1'] = 'integrate'
                else:
                    steps['Transform1'] = 'null_transform'
                imt_steps = imt_class_instance.steps
                imc_steps = imc_class_instance.steps
                steps.update(imt_steps)
                steps.update(imc_steps)
                steps['period'] = period
                steps['percentile'] = percentile
                steps['imc'] = imc
                steps['imt'] = imt
                pgm_steps[baseimt + '_' + baseimc] = steps
        return pgm_steps

    def execute_steps(self):
        """
        Executes the steps defined by the step_sets dictionary.

        Returns:
            pandas.Dataframe: Dataframe of all results.

        Notes:
            If a set of steps fail, then the error will be logged and the
            next step set will begin. The result cell of the dataframe will be
            filled with a np.nan value.
        """
        df = None
        for idx, imt_imc in enumerate(self.step_sets):
            step_set = self.step_sets[imt_imc]
            period = step_set['period']
            percentile = step_set['percentile']
            if period is not None:
                period = float(period)
            if percentile is not None:
                percentile = float(percentile)
            tseries = self.timeseries.copy()
            # paths
            transform_path = 'gmprocess.metrics.transform.'
            rotation_path = 'gmprocess.metrics.rotation.'
            combination_path = 'gmprocess.metrics.combination.'
            reduction_path = 'gmprocess.metrics.reduction.'
            try:
                # -------------------------------------------------------------
                # Transform 1
                t1_mod = importlib.import_module(
                    transform_path + step_set['Transform1'])
                t1_cls = self._get_subclass(inspect.getmembers(
                    t1_mod, inspect.isclass), 'Transform')
                t1 = t1_cls(tseries, self.damping, period, self._times).result

                # -------------------------------------------------------------
                # Transform 2
                t2_mod = importlib.import_module(
                    transform_path + step_set['Transform2'])
                t2_cls = self._get_subclass(inspect.getmembers(
                    t2_mod, inspect.isclass), 'Transform')
                t2 = t2_cls(t1, self.damping, period, self._times).result

                # -------------------------------------------------------------
                # Rotation
                rot_mod = importlib.import_module(
                    rotation_path + step_set['Rotation'])
                rot_cls = self._get_subclass(inspect.getmembers(
                    rot_mod, inspect.isclass), 'Rotation')
                rot = rot_cls(t2, self.event).result

                # -------------------------------------------------------------
                # Transform 3
                t3_mod = importlib.import_module(
                    transform_path + step_set['Transform3'])
                t3_cls = self._get_subclass(inspect.getmembers(
                    t3_mod, inspect.isclass), 'Transform')
                t3 = t3_cls(rot, self.damping, period, self._times).result

                # -------------------------------------------------------------
                # Combination 1
                c1_mod = importlib.import_module(
                    combination_path + step_set['Combination1'])
                c1_cls = self._get_subclass(inspect.getmembers(
                    c1_mod, inspect.isclass), 'Combination')
                c1 = c1_cls(t3).result

                # -------------------------------------------------------------
                # Reduction

                # * There is a problem here in that the percentile reduction
                #   step is not compatible with anything other than the max
                #   of either the time history or the oscillator.
                # * I think real solution is to have two reduction steps
                # * For now, I'm just going to disallow the percentile based
                #   methods with duration to avoid the incompatibility.
                # * Currently, the percentile reduction uses the length
                #   of c1 to decide if it needs to take the max of the
                #   data before applying the reduction.

                red_mod = importlib.import_module(
                    reduction_path + step_set['Reduction'])
                red_cls = self._get_subclass(inspect.getmembers(
                    red_mod, inspect.isclass), 'Reduction')
                red = red_cls(c1, self.bandwidth, percentile,
                              period, self.smooth_type).result

                # -------------------------------------------------------------
                # Combination 2
                c2_mod = importlib.import_module(
                    combination_path + step_set['Combination2'])
                c2_cls = self._get_subclass(inspect.getmembers(
                    c2_mod, inspect.isclass), 'Combination')
                c2 = c2_cls(red).result
            except Exception as e:
                msg = ('Error in calculation of %r: %r.\nResult '
                       'cell will be set to np.nan.' % (imt_imc, str(e)))
                logging.warning(msg)
                c2 = {'': np.nan}

            # we don't want to have separate columns for 'HN1' and 'HNN' and
            # 'BHN'. Instead we want all of these to be considered as simply
            # the "first horizontal channel".
            if 'channels' in imt_imc:
                new_c2 = {}
                for channel, value in c2.items():
                    if channel.endswith('1') or channel.endswith('N'):
                        newchannel = 'H1'
                    elif channel.endswith('2') or channel.endswith('E'):
                        newchannel = 'H2'
                    elif channel.endswith('Z'):
                        newchannel = 'Z'
                    else:
                        newchannel = channel
                    new_c2[newchannel] = value
            else:
                new_c2 = c2.copy()
            subdf = self._format(new_c2, step_set)
            if df is None:
                df = subdf
            else:
                df = pd.concat([df, subdf])
        return df

    def validate_stream(self):
        """
        Validates that the input is a StationStream, the units are either
        'vel' or 'acc', and the length of the traces are all equal.

        Railses:
            PGMException for the cases where:
                    1. The input is not a StationStream.
                    2. The units are not velocity or acceleration.
                    3. The length of the traces are not equal.
        """
        if not isinstance(self.timeseries, StationStream):
            raise PGMException("MetricsController: Input timeseries must be "
                               "a StationStream.")
        for idx, trace in enumerate(self.timeseries):
            units = trace.stats.standard.units
            trace_length = len(trace.data)
            if units.lower() != 'vel' and units.lower() != 'acc':
                raise PGMException("MetricsController: Trace units must be "
                                   "either 'vel' or 'acc'.")
            if idx == 0:
                standard_length = trace_length
            else:
                if trace_length != standard_length:
                    raise PGMException("MetricsController: Traces must all "
                                       "be the same length.")

    def _format(self, result, steps):
        """
        Creates a dataframe row(rows) structured as:
        imt imc result

        Args:
            result (dict):
                Result of the imt/imc calculation.
            steps (dict):
                The set of steps that are used to calculate 'result'.

        Returns:
            pandas.DataFrame: Dataframe listing the imc, imt, and result in
                    the following format:
                    |    IMT    |    IMC    |    Result    |
                    ----------------------------------------
                    |   <imt>   |   <imc>   |    <value>   |
        """
        dfdict = OrderedDict()
        dfdict['IMT'] = []
        dfdict['IMC'] = []
        dfdict['Result'] = []

        # We need the information about the type of imc/imt to
        # generate the appropirate strings that append period or percentile
        imc = steps['imc']
        imt = steps['imt']
        period = steps['period']
        percentile = steps['percentile']
        if period is not None:
            imt_str = '%s(%.3f)' % (imt.upper(), float(period))
        else:
            imt_str = imt.upper()
        if percentile is not None:
            imc_str = '%s(%s)' % (imc.upper(), float(percentile))
        else:
            imc_str = imc.upper()

        # For the cases such as channels or radial_transverse, where multiple
        # components are returned
        if imt == 'pga':
            multiplier = GAL_TO_PCTG
        else:
            multiplier = 1
        if len(result) > 1:
            for r in result:
                dfdict['IMT'] += [imt_str]
                dfdict['IMC'] += [r]
                dfdict['Result'] += [result[r] * multiplier]
        else:
            # Deal with nan values for channels and radial transverse
            if imc == 'radial_transverse' and '' in result:
                dfdict['IMT'] += [imt_str, imt_str]
                dfdict['IMC'] += ['HNR', 'HNT']
                dfdict['Result'] += [np.nan, np.nan]
            elif imc == 'channels' and '' in result:
                dfdict['IMT'] += [imt_str, imt_str, imt_str]
                dfdict['IMC'] += ['HN1', 'HN2', 'HNZ']
                dfdict['Result'] += [np.nan, np.nan, np.nan]
            else:
                dfdict['IMT'] += [imt_str]
                dfdict['IMC'] += [imc_str]
                for r in result:
                    dfdict['Result'] += [result[r] * multiplier]
        df = pd.DataFrame(data=dfdict)
        return df

    def _get_horizontal_time(self):
        """
        Get the 'times' array for a horizontal channel. This is required for
        spectral accelerations where a rotation (rotd) is requested.

        Returns:
            numpy.ndarray: Array of times for a horizontal channel.

        Raises:
            PGMException: if there are no horizontal channels.
        """
        for trace in self.timeseries:
            if 'Z' not in trace.stats['channel'].upper():
                times = trace.times()
                return times
        raise PGMException(
            'MetricsController: At least one horizontal '
            'channel is required for calculations of SA, ROTD, GMROTD, GM.'
        )

    def _get_subclass(self, classes, base_class):
        """
        Get the dynanically imported class required for the calculation step,
        while ignoring the base class.

        Args:
            classes (list): List of classes (string).
            base_class (string): Base class to ignore.

        Returns:
            class: Class for the calculation.
        """
        # The first item in the list is the string representation of the class
        # the second item is the class itself
        for cls_tupple in classes:
            if cls_tupple[0] != base_class and cls_tupple[0] != 'PGMException':
                return cls_tupple[1]

    def _parse_period(self, imt):
        """
        Parses the period from the imt.

        Args:
            imt (string): Imt that contains a period similar to one of the
                    following examples:
                            - SA(1.0)
                            - SA(1)
                            - SA1.0
                            - SA1
        Returns:
            string: Period for the calculation.

        Notes:
            Can be either a float or integer.
        """
        period = re.findall('\d+', imt)

        if len(period) > 1:
            period = '.'.join(period)
        elif len(period) == 1:
            period = period[0]
        else:
            period = None
        return period

    def _parse_percentile(self, imc):
        """
        Parses the percentile from the imc.

        Args:
            imc (string): Imc that contains a period similar to one of the
                    following examples:
                            - ROTD(50.0)
                            - ROTD(50)
                            - ROTD50.0
                            - ROTD50
        Returns:
            string: Period for the calculation.

        Notes:
            Can be either a float or integer.
        """
        percentile = re.findall('\d+', imc)
        if len(percentile) > 1:
            percentile = '.'.join(percentile)
        elif len(percentile) == 1:
            percentile = percentile[0]
        else:
            percentile = None
        return percentile
