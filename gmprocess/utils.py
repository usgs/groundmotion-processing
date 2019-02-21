#!/usr/bin/env python
"""
Module for general-purpose methods that do not have a more specific home.
"""
from collections import OrderedDict


def _update_params(trace, process_type, parameters):
    """
    Helper function to update a trace's processing_parameters.

    Args:
        trace (obspy.core.trace.Trace):
            Trace of strong motion dataself.
        process_type (str):
            Key for processing_parameters subdictionary.
        parameters (dict or list):
            Parameters for the given key.

    Returns:
        obspy.core.trace.Trace: Trace with updated processing_parameters.
    """
    if 'processing_parameters' not in trace.stats:
        trace.stats['processing_parameters'] = OrderedDict()
    trace.stats['processing_parameters'][process_type] = parameters
    return trace
