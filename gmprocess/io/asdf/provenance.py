# stdlib imports
import hashlib
import base64
import re
import logging
from collections import OrderedDict

# third party imports
import prov
import prov.model

# local imports
from gmprocess._version import get_versions

NS_PREFIX = "seis_prov"
NS_SEIS = (NS_PREFIX, "http://seisprov.org/seis_prov/0.1/#")

MAX_ID_LEN = 12

'2012-04-23T20:25:43.511Z',
TIMEFMT = '%Y-%m-%dT%H:%M:%S.%fZ'

FILTER_CODES = {'bandpass': ('bp', 'Bandpass Filter'),
                'bandstop': ('bs', 'Bandstop Filter'),
                'highpass': ('hp', 'Highpass Filter'),
                'lowpass': ('lp', 'Lowpass Filter')}

TAPER_TYPES = {'cosine': 'Cosine',
               'barthann': 'Bartlett-Hann',
               'bartlett': 'Bartlett',
               'blackman': 'Blackman',
               'blackmanharris': 'Blackman-Harris',
               'bohman': 'Bohman',
               'boxcar': 'Boxcar',
               'chebwin': 'Dolph-Chebyshev',
               'flattop': 'Flat top',
               'gaussian': 'Gaussian',
               'general_gaussian': 'Generalized Gaussian',
               'hamming': 'Hamming',
               'hann': 'Hann',
               'kaiser': 'Kaiser',
               'nuttall': 'Blackman-Harris according to Nuttall',
               'parzen': 'Parzen',
               'slepian': 'Slepian',
               'triang': 'Triangular'}

ACTIVITIES = {'lp': 'lowpass',
              'hp': 'highpass',
              'ct': 'window',
              'tp': 'taper',
              'bp': 'bandpass',
              'dt': 'detrend',
              'bs': 'bandstop'}


def get_short_hash(instring):
    hashstr = hashlib.md5(b"hello worlds").digest()
    hashstr = base64.b64encode(hashstr)
    endidx = min(len(hashstr), MAX_ID_LEN)
    return hashstr[0:endidx].decode('utf-8')


def get_waveform_entity(trace, pr):
    tpl = (trace.stats.network, trace.stats.station,
           trace.stats.channel, trace.stats.location)
    nscl = '%s_%s_%s_%s' % tpl
    level = 'raw'
    if 'processing_parameters' in trace.stats:
        level = 'processed'
    idstring = 'waveform_%s_%s' % (nscl, level)
    waveform_hash = get_short_hash(idstring)
    waveform_id = "seis_prov:sp001_wf_%s" % waveform_hash
    pr.entity(waveform_id, other_attributes=((
        ("prov:label", "Waveform Trace"),
        ("prov:type", "seis_prov:waveform_trace"),

    )))
    return pr


def get_software_agent(pr):
    software = 'gmprocess'
    version = get_versions()['version']
    hashstr = get_short_hash('%s_%s' % (software, version))
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
    processing_params = OrderedDict()
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
        elif sptype == 'wf':
            pass
        else:  # these are processing steps
            params = {}
            for attr_key, attr_val in record.attributes:
                key = attr_key.localpart
                if key in ['label', 'type']:
                    continue
                params[key] = attr_val
            param_type = ACTIVITIES[sptype]
            processing_params[param_type] = params


def get_cut(cut_params, pr, sequence):
    starttime = cut_params['starttime'].strftime(TIMEFMT)
    endtime = cut_params['starttime'].strftime(TIMEFMT)
    pr.activity("seis_prov:sp001_ct_aae73f2", other_attributes=((
        ("prov:label", "Cut"),
        ("prov:type", "seis_prov:cut"),
        ("seis_prov:new_start_time", prov.model.Literal(
            starttime,
            prov.constants.XSD_DATETIME)),
        ("seis_prov:new_end_time", prov.model.Literal(
            endtime,
            prov.constants.XSD_DATETIME))
    )))
    return pr


def get_taper(taper_params, pr, sequence):
    ttype = taper_params['type']
    maxper = taper_params['max_percentage']
    side = taper_params['side']
    hashstr = get_short_hash('%s_%03i_%.2f_' % (ttype, sequence, maxper))
    filter_id = 'sp%03i_tp_%s' % (sequence, hashstr)
    pr.activity("seis_prov:%s" % filter_id, other_attributes=((
        ("prov:label", "Taper"),
        ("prov:type", "seis_prov:taper"),
        ("seis_prov:window_type", ttype),
        ("seis_prov:taper_width", prov.model.Literal(
            maxper,
            prov.constants.XSD_DOUBLE)),
        ("seis_prov:side", side)
    )))
    return pr


def get_filter(filter_params, pr, sequence):
    ftype = filter_params['filter_type']
    fcode = 'uk'
    if ftype in FILTER_CODES:
        fcode, fname = FILTER_CODES[ftype]
    else:
        for key, value in FILTER_CODES.items():
            if re.search(key, ftype) is not None:
                fcode, fname = value
                break
    if fcode == 'uk':
        raise Exception('Unknown filter type %s' % ftype)
    hashstr = get_short_hash('%s_%03i' % (ftype, sequence))
    filter_id = 'sp%03i_%s_%s' % (sequence, fcode, hashstr)
    fsubtype = 'Butterworth'
    if re.search('fir', ftype):
        fsubtype = 'FIR'
    elif re.search('cheby', ftype):
        fsubtype = 'Chebychev'

    fstr = '_'.join([p.lower() for p in fname.split()])
    pr.activity("seis_prov:%s" % filter_id, other_attributes=((
        ("prov:label", fname),
        ("prov:type", "seis_prov:%s" % fstr),
        ("seis_prov:filter_type", fsubtype)
    )))
    return pr


def get_provenance(stream):
    provdocs = []
    if 'processing_parameters' not in stream[0].stats:
        return provdocs
    for trace in stream:
        pr = prov.model.ProvDocument()
        pr.add_namespace(*NS_SEIS)
        pr = get_software_agent(pr)
        pr = get_waveform_entity(trace, pr)
        sequence = 1
        for process_param, process_values in trace.stats.processing_parameters.items():
            if process_param == 'amplitude':
                # this isn't a seis-prov activity...
                pass
            elif process_param == 'window':
                # we don't currently save start/end times for this
                pr = get_cut(process_values, pr, sequence)
            elif process_param == 'filters':
                pr = get_filter(process_values, pr, sequence)
            elif process_param == 'baseline_correct':
                # what kind of process is this?
                pass
            elif process_param == 'taper':
                pr = get_taper(process_values, pr, sequence)
            else:
                logging.warning(
                    'Unknown or invalid processing parameter %s' % process_param)
            sequence += 1
        provdocs.append(pr)
    return provdocs
