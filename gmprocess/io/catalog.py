#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import requests


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
        out_catalog (list): Catalogs (str) to convert ids options include: UNID, EMSC, INGV, USGS, ISC, or ALL.
        collect_dloc (float): dloc parameter.
        collect_dtmie (float): dtime parameter.
        misfit_dloc (float): Misfit delta_loc parameter.
        misit_dtime (float): Misfit delta_time parameter.
        misfit_dmag (float): Misfit delta_mag parameter.
        preferred_only (str): Select only the first event by catalog if 'true'.
        include_info (str): Return info about the event if 'true'.
        return_json (bool): Whether or not to return the entire JSON.

    Returns:
        dict: Returns a dictionary mapping catalogs to event IDS if return_json is False.
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
