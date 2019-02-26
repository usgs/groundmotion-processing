#!/usr/bin/env python
"""
Module for general-purpose methods that do not have a more specific home.
"""


def _get_provenance(trace, prov_id):
    matching_params = []
    for param_dict in trace.stats.processing_parameters:
        if param_dict['prov_id'] == prov_id:
            matching_params.append(param_dict['prov_attributes'])
    return matching_params


def _update_provenance(trace, prov_id, prov_attributes):
    """
    Helper function to update a trace's processing_parameters.

    Args:
        trace (obspy.core.trace.Trace):
            Trace of strong motion dataself.
        prov_id (str):
            Key for processing_parameters subdictionary.
        prov_attributes (dict or list):
            Parameters for the given key.

    Returns:
        obspy.core.trace.Trace: Trace with updated processing_parameters.
            Processing parameters are stored as a list under the Trace.stats
            dictionary, with each entry consisting of a dictionary with keys
            'prov_id' and 'prov_attributes'.
    """
    if 'processing_parameters' not in trace.stats:
        trace.stats['processing_parameters'] = []
    processing_dict = {'prov_id': prov_id,
                       'prov_attributes': prov_attributes}
    trace.stats['processing_parameters'].append(processing_dict)
    return trace
