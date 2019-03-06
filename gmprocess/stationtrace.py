# stdlib imports
import json

# third party imports
import numpy as np
from obspy.core.trace import Trace

UNITS = {'acc': 'cm/s/s',
         'vel': 'cm/s'}
REVERSE_UNITS = {'cm/s/s': 'acc',
                 'cm/s': 'vel'}

PROCESS_LEVELS = {'V0': 'raw counts',
                  'V1': 'uncorrected physical units',
                  'V2': 'corrected physical units',
                  'V3': 'derived time series'}


STANDARD_KEYS = {
    'source': {
        'type': str,
        'required': True,
        'default': ''
    },
    'horizontal_orientation': {
        'type': float,
        'required': False,
        'default': np.nan
    },
    'station_name': {
        'type': str,
        'required': False,
        'default': ''
    },
    'instrument_period': {
        'type': float,
        'required': False,
        'default': np.nan
    },
    'instrument_damping': {
        'type': float,
        'required': False,
        'default': np.nan
    },
    'process_time': {
        'type': str,
        'required': False,
        'default': ''
    },
    'process_level': {
        'type': str,
        'required': True,
        'default': list(PROCESS_LEVELS.values())
    },
    'sensor_serial_number': {
        'type': str,
        'required': False,
        'default': ''
    },
    'instrument': {
        'type': str,
        'required': False,
        'default': ''
    },
    'structure_type': {
        'type': str,
        'required': False,
        'default': ''
    },
    'corner_frequency': {
        'type': float,
        'required': False,
        'default': np.nan
    },
    'units': {
        'type': str,
        'required': True,
        'default': ''
    },
    'source_format': {
        'type': str,
        'required': True,
        'default': ''
    },
    'comments': {
        'type': str,
        'required': False,
        'default': ''
    },
}

INT_TYPES = [np.dtype('int8'),
             np.dtype('int16'),
             np.dtype('int32'),
             np.dtype('int64'),
             np.dtype('uint8'),
             np.dtype('uint16'),
             np.dtype('uint32'),
             np.dtype('uint64')]

FLOAT_TYPES = [np.dtype('float32'),
               np.dtype('float64')]

TIMEFMT = '%Y-%m-%dT%H:%M:%SZ'
TIMEFMT_MS = '%Y-%m-%dT%H:%M:%S.%fZ'


class StationTrace(Trace):
    """Subclass of Obspy Trace object which holds more metadata.

    """

    def __init__(self, data=np.array([]), header=None, inventory=None):
        """Construct StationTrace.

        Args:
            data (ndarray):
                numpy array of points.
            header (dict-like):
                Dictionary of metadata (see trace.stats docs).
            inventory (Inventory):
                Obspy Inventory object.
        """
        if inventory is None and header is None:
            raise Exception(
                'Cannot create StationTrace without header info or Inventory')
        if inventory is not None and header is not None:
            channelid = header['channel']
            (response, standard,
             coords, format_specific) = _stats_from_inventory(data, inventory,
                                                              channelid)
            header['response'] = response
            header['coordinates'] = coords
            header['standard'] = standard
            header['format_specific'] = format_specific
        super(StationTrace, self).__init__(data=data, header=header)
        self.provenance = []
        self.parameters = {}
        self.validate()

    def validate(self):
        """Ensure that all required metadata fields have been set.

        Raises:
            KeyError:
                - When standard dictionary is missing required fields
                - When standard values are of the wrong type
                - When required values are set to a default.
        """
        # are all of the defined standard keys in the standard dictionary?
        req_keys = set(STANDARD_KEYS.keys())
        std_keys = set(list(self.stats.standard.keys()))
        if not req_keys <= std_keys:
            missing = str(req_keys - std_keys)
            raise KeyError(
                'Missing standard values in StationTrace header: "%s"'
                % missing)
        type_errors = []
        required_errors = []
        for key in req_keys:
            keydict = STANDARD_KEYS[key]
            value = self.stats.standard[key]
            required = keydict['required']
            vtype = keydict['type']
            default = keydict['default']
            if not isinstance(value, vtype):
                type_errors.append(key)
            if required:
                if isinstance(default, list):
                    if value not in default:
                        required_errors.append(key)
                if value == default:
                    required_errors.append(key)

        type_error_msg = ''
        if len(type_errors):
            fmt = 'The following standard keys have the wrong type: "%s"'
            tpl = ','.join(type_errors)
            type_error_msg = fmt % tpl

        required_error_msg = ''
        if len(required_errors):
            fmt = 'The following standard keys have the wrong type: "%s"'
            tpl = ','.join(required_errors)
            required_error_msg = fmt % tpl

        error_msg = type_error_msg + '\n' + required_error_msg
        if len(error_msg.strip()):
            raise KeyError(error_msg)

    def getProvenanceKeys(self):
        """Get a list of all available provenance keys.

        Returns:
            list: List of available provenance keys.
        """
        if not len(self.provenance):
            return []
        pkeys = []
        for provdict in self.provenance:
            pkeys.append(provdict['prov_id'])
        return pkeys

    def getProvenance(self, prov_id):
        """Get list of seis-prov compatible attributes whose id matches prov_id.

        # activities.
        See http://seismicdata.github.io/SEIS-PROV/_generated_details.html

        Args:
            prov_id (str):
                Provenance ID (see URL above).

        Returns:
            list: Sequence of prov_attribute dictionaries (see URL above).
        """
        matching_prov = []
        if not len(self.provenance):
            return matching_prov
        for provdict in self.provenance:
            if provdict['prov_id'] == prov_id:
                matching_prov.append(provdict['prov_attributes'])
        return matching_prov

    def setProvenance(self, prov_id, prov_attributes):
        """Update a trace's provenance information.

        Args:
            trace (obspy.core.trace.Trace):
                Trace of strong motion dataself.
            prov_id (str):
                Activity prov:id (see URL above).
            prov_attributes (dict or list):
                Activity attributes for the given key.
        """
        provdict = {'prov_id': prov_id,
                    'prov_attributes': prov_attributes}
        self.provenance.append(provdict)

    def getAllProvenance(self):
        """Get internal list of processing history.

        Returns:
            list:
                Sequence of dictionaries containing fields:
                - prov_id Activity prov:id (see URL above).
                - prov_attributes Activity attributes for the given key.
        """
        return self.provenance

    def hasParameter(self, param_id):
        """Check to see if Trace contains a given parameter.

        Args:
            param_id (str): Name of parameter to check.

        Returns:
            bool: True if parameter is set, False if not.
        """
        return param_id in self.parameters

    def setParameter(self, param_id, param_attributes):
        """Add to the StationTrace's set of arbitrary metadata.

        Args:
            param_id (str):
                Key for parameters dictionary.
            param_attributes (dict or list):
                Parameters for the given key.
        """
        self.parameters[param_id] = param_attributes

    def getParameterKeys(self):
        """Get a list of all available parameter keys.

        Returns:
            list: List of available parameter keys.
        """
        return list(self.parameters.keys())

    def getParameter(self, param_id):
        """Retrieve some arbitrary metadata.

        Args:
            param_id (str):
                Key for parameters dictionary.

        Returns:
            dict or list:
                Parameters for the given key.
        """
        if param_id not in self.parameters:
            raise KeyError(
                'Parameter %s not found in StationTrace' % param_id)
        return self.parameters[param_id]


def _stats_from_inventory(data, inventory, channelid):
    if len(inventory.source):
        source = inventory.source
    station = inventory.networks[0].stations[0]
    coords = {'latitude': station.latitude,
              'longitude': station.longitude,
              'elevation': station.elevation}
    channel_names = [ch.code for ch in station.channels]
    channelidx = channel_names.index(channelid)
    channel = station.channels[channelidx]

    standard = {}

    # things we'll never get from an inventory object
    standard['corner_frequency'] = np.nan
    standard['instrument_damping'] = np.nan
    standard['instrument_period'] = np.nan
    standard['structure_type'] = ''
    standard['process_time'] = ''

    if data.dtype in INT_TYPES:
        standard['process_level'] = 'raw counts'
    else:
        standard['process_level'] = 'uncorrected physical units'

    standard['source'] = source
    standard['instrument'] = ''
    standard['sensor_serial_number'] = ''
    if channel.sensor is not None and channel.sensor.type != 'None':
        standard['instrument'] = channel.sensor.type
        if channel.sensor.serial_number != 'None':
            standard['sensor_serial_number'] = channel.sensor.serial_number
        else:
            standard['sensor_serial_number'] = ''

    if channel.azimuth is not None:
        standard['horizontal_orientation'] = channel.azimuth

    standard['source_format'] = channel.storage_format
    if standard['source_format'] is None:
        standard['source_format'] = 'fdsn'

    standard['units'] = ''
    if channelid[1] == 'N':
        standard['units'] = 'acc'
    else:
        standard['units'] = 'vel'

    if len(channel.comments):
        standard['comments'] = channel.comments[0]
    else:
        standard['comments'] = ''
    if station.site.name != 'None':
        standard['station_name'] = station.site.name
    # extract the remaining standard info and format_specific info
    # from a JSON string in the station description.

    format_specific = {}
    if station.description is not None and station.description != 'None':
        jsonstr = station.description
        big_dict = json.loads(jsonstr)
        standard.update(big_dict['standard'])
        format_specific = big_dict['format_specific']

    response = None
    if channel.response is not None:
        response = channel.response

    return (response, standard, coords, format_specific)
