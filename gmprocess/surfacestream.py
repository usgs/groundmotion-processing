"""Stream for dense waveform data on a surface.

:TODO: This is an incomplete implementation of SurfaceStream.

Issues:
  1. We are likely missing important metadata that will be needed for
     processing.

  2. It would be good to refactor the provenance storage/access. There is
     a significant overlab with StationTrace and StationStream.
"""

# stdlib imports
import json
import logging

# third party imports
import numpy
from obspy.core.utcdatetime import UTCDateTime
from obspy.core.inventory import Comment


UNITS = {
    'acc': 'cm/s/s',
    'vel': 'cm/s'
}
REVERSE_UNITS = {
    'cm/s/s': 'acc',
    'cm/s': 'vel'
}


class SurfaceStream(object):
    """Stream for dense waveform data on a surface.

    The surface is defined by its geometry and topology. The geometry
    corresponds to the coordinates of the vertices on the
    surface. The topology corresponds to the how the vertices are connected
    into cells. For a finite-difference grid the cells are quadrilaterals. For
    a triangulated surface, the cells are triangles.
    """

    def __init__(self, data=None, geometry=None, topology=None):
        """Constructor.

        Args:
            data (numpy.array):
                Data on surface [num_time, num_points, 3].
            geometry (numpy.array):
                Coordinates of vertices on surface [num_points, 3].
            topology (numpy.array):
                Cells connecting vertices on surface [num_cells, num_corners].
        """
        super().__init__()
        self.parameters = {}
        self.data = data
        self.geometry = geometry
        self.topology = topology
        self.provenance = []
        # self.validate()

    @property
    def passed(self):
        """
        Check whether the stream has failed any processing steps.

        Returns:
            bool: True if no failures, False otherwise.
        """
        return self.check_stream()

    def __str__(self, extended=False, indent=0):
        """
        String summary of the SurfaceStream.

        Args:
            extended (bool):
                Unused; kept for compatibility with ObsPy parent class.
            indent (int):
                Number of characters to indent.
        """
        if self.passed:
            status = ' (passed)'
        else:
            status = ' (failed)'
        ind_str = ' ' * indent
        out = '{npoints} surface points in SurfaceStream with {ntime} time points{status}\n'.format(
            npoints=data.shape[1], ntime=data.shape[0], status=status)
        return out

    def setStreamParam(self, param_id, param_attributes):
        """Add to the SurfaceStreams's set of arbitrary metadata.

        Args:
            param_id (str):
                Key for parameters dictionary.
            param_attributes (dict or list):
                Parameters for the given key.
        """
        self.parameters[param_id] = param_attributes

    def getStreamParamKeys(self):
        """Get a list of all available parameter keys.

        Returns:
            list: List of available parameter keys.
        """
        return list(self.parameters.keys())

    def getStreamParam(self, param_id):
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
                "Parameter '{}' not found in SurfaceStream.".format(param_id))
        return self.parameters[param_id]

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
        self.validate()

    def getAllProvenance(self):
        """Get internal list of processing history.

        Returns:
            list:
                Sequence of dictionaries containing fields:
                - prov_id Activity prov:id (see URL above).
                - prov_attributes Activity attributes for the given key.
        """
        return self.provenance

    def getProvenanceDocument(self, base_prov=None):
        if base_prov is None:
            pr = prov.model.ProvDocument()
            pr.add_namespace(*NS_SEIS)
            pr = _get_person_agent(pr)
            pr = _get_software_agent(pr)
            pr = _get_waveform_entity(self, pr)
        else:
            pr = _get_waveform_entity(self, copy.deepcopy(base_prov))
        sequence = 1
        for provdict in self.getAllProvenance():
            provid = provdict['prov_id']
            prov_attributes = provdict['prov_attributes']
            if provid not in ACTIVITIES:
                fmt = 'Unknown or invalid processing parameter %s'
                logging.debug(fmt % provid)
                continue
            pr = _get_activity(pr, provid, prov_attributes, sequence)
            sequence += 1
        return pr

    def setProvenanceDocument(self, provdoc):
        software = {}
        person = {}
        for record in provdoc.get_records():
            ident = record.identifier.localpart
            parts = ident.split('_')
            sptype = parts[1]
            # hashid = '_'.join(parts[2:])
            # sp, sptype, hashid = ident.split('_')
            if sptype == 'sa':
                for attr_key, attr_val in record.attributes:
                    key = attr_key.localpart
                    if isinstance(attr_val, prov.identifier.Identifier):
                        attr_val = attr_val.uri
                    software[key] = attr_val
            elif sptype == 'pp':
                for attr_key, attr_val in record.attributes:
                    key = attr_key.localpart
                    if isinstance(attr_val, prov.identifier.Identifier):
                        attr_val = attr_val.uri
                    person[key] = attr_val
            elif sptype == 'wf':  # waveform tag
                continue
            else:  # these are processing steps
                params = {}
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
                self.setProvenance(sptype, params)
            self.setParameter('software', software)
            self.setParameter('user', person)

    def check_stream(self):
        """Processing checks get recorded as a 'failure' parameter.

        Returns:
            bool: False if stream has failed any checks, True otherwise.
        """
        return False if hasParameter('failure') else True
