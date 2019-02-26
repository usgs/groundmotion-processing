# stdlib imports
import hashlib
import base64
import logging
from datetime import datetime
from collections import OrderedDict

# third party imports
import prov
import prov.model
from obspy.core.utcdatetime import UTCDateTime

# local imports
from gmprocess._version import get_versions

NS_PREFIX = "seis_prov"
NS_SEIS = (NS_PREFIX, "http://seisprov.org/seis_prov/0.1/#")

MAX_ID_LEN = 12

TIMEFMT = '%Y-%m-%dT%H:%M:%S.%fZ'

ACTIVITIES = {'waveform_simulation': {'code': 'ws',
                                      'label': 'Waveform Simulation'},
              'taper': {'code': 'tp', 'label': 'Taper'},
              'stack_cross_correlations': {'code': 'sc',
                                           'label': 'Stack Cross Correlations'},
              'simulate_response': {'code': 'sr', 'label': 'Simulate Response'},
              'rotate': {'code': 'rt', 'label': 'Rotate'},
              'resample': {'code': 'rs', 'label': 'Resample'},
              'remove_response': {'code': 'rr', 'label': 'Remove Response'},
              'pad': {'code': 'pd', 'label': 'Pad'},
              'normalize': {'code': 'nm', 'label': 'Normalize'},
              'multiply': {'code': 'nm', 'label': 'Multiply'},
              'merge': {'code': 'mg', 'label': 'Merge'},
              'lowpass_filter': {'code': 'lp', 'label': 'Lowpass Filter'},
              'interpolate': {'code': 'ip', 'label': 'Interpolate'},
              'integrate': {'code': 'ig', 'label': 'Integrate'},
              'highpass_filter': {'code': 'hp', 'label': 'Highpass Filter'},
              'divide': {'code': 'dv', 'label': 'Divide'},
              'differentiate': {'code': 'df', 'label': 'Differentiate'},
              'detrend': {'code': 'dt', 'label': 'Detrend'},
              'decimate': {'code': 'dc', 'label': 'Decimate'},
              'cut': {'code': 'ct', 'label': 'Cut'},
              'cross_correlate': {'code': 'co', 'label': 'Cross Correlate'},
              'calculate_adjoint_source': {'code': 'ca',
                                           'label': 'Calculate Adjoint Source'},
              'bandstop_filter': {'code': 'bs', 'label': 'Bandstop Filter'},
              'bandpass_filter': {'code': 'bp', 'label': 'Bandpass Filter'}
              }


def _get_short_hash(instring):
    '''Get a 12 character (maybe) unique hash for an input string.

    Args:
        instring (str): 
            Any string.

    Returns:
        str: First 12 characters of md5 hash of input string.
    '''
    hashstr = hashlib.md5(b"hello worlds").digest()
    hashstr = base64.b64encode(hashstr)
    endidx = min(len(hashstr), MAX_ID_LEN)
    return hashstr[0:endidx].decode('utf-8')


def _get_waveform_entity(trace, pr):
    '''Get the seis-prov entity for an input Trace.

    Args:
        trace (Trace): 
            Input Obspy Trace object.
        pr (Prov): 
            prov.model.ProvDocument

    Returns:
        prov.model.ProvDocument:
            Provenance document updated with waveform entity information.
    '''
    tpl = (trace.stats.network, trace.stats.station,
           trace.stats.channel, trace.stats.location)
    nscl = '%s_%s_%s_%s' % tpl
    level = 'raw'
    if 'processing_parameters' in trace.stats:
        level = 'processed'
    idstring = 'waveform_%s_%s' % (nscl, level)
    waveform_hash = _get_short_hash(idstring)
    waveform_id = "seis_prov:sp001_wf_%s" % waveform_hash
    pr.entity(waveform_id, other_attributes=((
        ("prov:label", "Waveform Trace"),
        ("prov:type", "seis_prov:waveform_trace"),

    )))
    return pr


def _get_software_agent(pr):
    '''Get the seis-prov entity for the gmprocess software.

    Args:
        pr (prov.model.ProvDocument): 
            Existing ProvDocument.

    Returns:
        prov.model.ProvDocument:
            Provenance document updated with gmprocess software name/version.
    '''
    software = 'gmprocess'
    version = get_versions()['version']
    hashstr = _get_short_hash('%s_%s' % (software, version))
    agent_id = "seis_prov:sp001_sa_%s" % hashstr
    giturl = 'https://github.com/usgs/groundmotion-processing'
    pr.agent(agent_id, other_attributes=((
        ("prov:label", software),
        ("prov:type", prov.identifier.QualifiedName(
            prov.constants.PROV, "SoftwareAgent")),
        ("seis_prov:software_name", software),
        ("seis_prov:software_version", version),
        ("seis_prov:website", prov.model.Literal(
            giturl,
            prov.constants.XSD_ANYURI)),
    )))
    return pr


def extract_provenance(pr):
    '''Extract provenance information from an existing ProvDocument data structure.

    Args:
        pr (prov.model.ProvDocument):
            Existing provenance document extracted from an ASDF file.

    Returns:
        list: 
            Sequence of dictionaries with keys 'prov_id' and 'prov_attributes'. The value for the latter key
            is another dictionary of the attributes associated with the type of operation. See 
            http://seismicdata.github.io/SEIS-PROV/_generated_details.html#activities.
    '''
    processing_params = []
    software = {}
    for record in pr.get_records():
        ident = record.identifier.localpart
        sp, sptype, hashid = ident.split('_')
        if sptype == 'sa':
            for attr_key, attr_val in record.attributes:
                key = attr_key.localpart
                if isinstance(attr_val, prov.identifier.Identifier):
                    attr_val = attr_val.uri
                software[key] = attr_val
        elif sptype == 'wf':  # waveform tag
            continue
        else:  # these are processing steps
            params = {}
            paramdict = {}
            sptype = ''
            for attr_key, attr_val in record.attributes:
                key = attr_key.localpart
                if key == 'label':
                    continue
                elif key == 'type':
                    _, sptype = attr_val.split(':')
                    continue
                if isinstance(attr_val, datetime):
                    attr_val = UTCDateTime(attr_val)
                params[key] = attr_val
            paramdict['prov_id'] = sptype
            paramdict['prov_attributes'] = params
            processing_params.append(paramdict)
    return (processing_params, software)


def _get_activity(pr, activity, attributes, sequence):
    '''Get the seis-prov entity for an input processing "activity".

    See
    http://seismicdata.github.io/SEIS-PROV/_generated_details.html#activities

    for details on the types of activities that are possible to capture.


    Args:
        pr (prov.model.ProvDocument): 
            Existing ProvDocument.
        activity (str): 
            The prov:id for the input activity.
        attributes (dict):
            The attributes associated with the activity.
        sequence (int): 
            Integer used to identify the order in which the activities were performed.
    Returns:
        prov.model.ProvDocument:
            Provenance document updated with input activity.
    '''
    activity_dict = ACTIVITIES[activity]
    hashstr = '%s' % activity
    hashid = _get_short_hash(hashstr)
    code = activity_dict['code']
    label = activity_dict['label']
    activity_id = 'sp%03i_%s_%s' % (sequence, code, hashid)
    pr_attributes = [('prov:label', label),
                     ('prov:type', 'seis_prov:%s' % activity)]
    for key, value in attributes.items():
        if isinstance(value, float):
            value = prov.model.Literal(value, prov.constants.XSD_DOUBLE)
        elif isinstance(value, int):
            value = prov.model.Literal(value,
                                       prov.constants.XSD_INT)
        elif isinstance(value, UTCDateTime):
            value = prov.model.Literal(value.strftime(TIMEFMT),
                                       prov.constants.XSD_DATETIME)

        att_tuple = ('seis_prov:%s' % key, value)
        pr_attributes.append(att_tuple)
    pr.activity('seis_prov:%s' % activity_id,
                other_attributes=pr_attributes)

    return pr


def get_provenance(stream):
    '''Get a list of ProvDocuments from an input stream.

    Args:
        stream (Stream):
            Input Obspy Stream where Traces contain a processing_parameters list.

    Returns:
        list: Sequence of ProvDocument objects where processing activity has been documented.
    '''
    provdocs = []
    if 'processing_parameters' not in stream[0].stats:
        return provdocs
    for trace in stream:
        pr = prov.model.ProvDocument()
        pr.add_namespace(*NS_SEIS)
        pr = _get_software_agent(pr)
        pr = _get_waveform_entity(trace, pr)
        sequence = 1
        provdicts = trace.stats.processing_parameters
        for provdict in provdicts:
            provid = provdict['prov_id']
            if provid not in ACTIVITIES:
                fmt = 'Unknown or invalid processing parameter %s'
                logging.debug(fmt % provid)
                continue
            prov_attributes = provdict['prov_attributes']
            pr = _get_activity(pr, provid, prov_attributes, sequence)
            sequence += 1
        provdocs.append(pr)
    return provdocs
