#!/usr/bin/env python3

# stdlib imports
import requests

# third party imports
from lxml import etree


INGV_CATALOGS = ['INGV', 'ESM', 'CNT']
VALID_CATALOGS = ['UNID', 'EMSC', 'INGV', 'USGS', 'ISC', 'CNT', 'ESM']


def convert_ids(source_id, source_catalog, out_catalog, collect_dloc=1.5,
                collect_dtime=60, misfit_dloc=105, misfit_dtime=13,
                misfit_dmag=0.8, preferred_only=None, include_info=None,
                return_json=None):
    """
    This function will convert an event ID between the UNID, EMSC, INGV,
    USGS, and ISC catalogs.

    Args:
        source_id (str): Event ID from the source catalog.
        source_catalog (str): Source catalog (UNID, EMSC, INGV, USGS or ISC).
        out_catalog (list): Catalogs (str) to convert ids
                options include: UNID, EMSC, INGV, USGS, ISC, or ALL.
        collect_dloc (float): dloc parameter.
        collect_dtmie (float): dtime parameter.
        misfit_dloc (float): Misfit delta_loc parameter.
        misit_dtime (float): Misfit delta_time parameter.
        misfit_dmag (float): Misfit delta_mag parameter.
        preferred_only (str): Select only the first event by catalog if 'true'.
        include_info (str): Return info about the event if 'true'.
        return_json (bool): Whether or not to return the entire JSON.

    Returns:
        dict: Returns a dictionary mapping catalogs to event IDS if return_json
              is False.
        list: Returns a list of the JSON if return_json is true.
    """
    source_catalog = source_catalog.upper()
    if source_catalog not in VALID_CATALOGS:
        raise Exception('Not a valid source_catalog choice. Valid catalogs '
                        'include %s' % VALID_CATALOGS)

    all_catalogs = False
    if isinstance(out_catalog, str):
        if out_catalog.upper() == 'ALL':
            all_catalogs = True
        out_catalog = [out_catalog]
    elif 'all' in out_catalog or 'ALL' in out_catalog:
        all_catalogs = True

    arg_dict = locals().copy()
    arg_dict['out_catalog'] = 'all'

    r = requests.get('http://www.seismicportal.eu/eventid/api/convert',
                     params=arg_dict)

    output = r.json()

    if output is None:
        raise Exception('No matching event IDs were found.')

    if return_json is True:
        return output
    else:
        catalog_id_dict = dict()
        if all_catalogs:
            for d in output:
                catalog_id_dict[d['catalog']] = d['id']
        else:
            for cat in out_catalog:
                for d in output:
                    if cat.upper() in d['catalog']:
                        catalog_id_dict[cat.upper()] = d['id']
            if len(catalog_id_dict.keys()) == 1 and len(out_catalog) == 1:
                catalog_id = catalog_id_dict.popitem()[1]
                return catalog_id
            if len(catalog_id_dict.keys()) == 0:
                raise Exception(
                    'No event ids found. Check that the '
                    'source_catalog and out_catalog values are valid.')
        return catalog_id_dict


def get_ingv_shakemap(eventid, catalog='INGV', output_format='event_dat',
                      flag='0'):
    """
    Retrieve a ShakeMap xml file from the INGV catalog.

    Args:
        eventid (str): Event identification code from the specified catalog.
        catalog (str): Catalog code. Default is 'INGV'.
        output_format (str): Format of the retrieved data. 'event' will return
                a short event description; 'event_data' will return the full
                ShakeMap xml. Default is 'event_data'.
        flag (str): Data flag. '0' will not return data flaged as problematic;
                'all' will return all data including flagged data. Flagged
                data is marked with flag=1 in the xml. Default is '0'.

    Returns:
        etree._Element: lxml element containing shakemap-data and stationlist.
    """
    valid_formats = ['event', 'event_dat']
    valid_flags = ['0', 'all']
    catalog = catalog.upper()
    output_format = output_format.lower()
    flag = flag.lower()

    if catalog not in INGV_CATALOGS:
        raise Exception('Not a valid catalog choice. Valid catalogs include '
                        '%s' % INGV_CATALOGS)
    elif output_format not in valid_formats:
        raise Exception('Not a valid format choice. Valid formats include '
                        '%s' % valid_formats)
    elif flag not in valid_flags:
        raise Exception('Not a valid flag choice. Valid flags include '
                        '%s' % valid_flags)

    arg_dict = locals()
    del arg_dict['output_format']
    arg_dict['format'] = output_format

    url = 'http://webservices.ingv.it/ingvws/shakedata/1/query'
    r = requests.get(url, params=arg_dict)

    if r.status_code != 200:
        raise Exception(r.json()['error']['message'])

    station_list = etree.fromstring(r.content)
    shakemap_xml = etree.Element('shakemap-data', code_version="3.5",
                                 map_version="3")
    shakemap_xml.insert(0, station_list)
    return shakemap_xml
