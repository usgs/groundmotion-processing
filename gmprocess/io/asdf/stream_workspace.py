# stdlib imports
import json
import re

# third party imports
import pyasdf
import numpy as np
from obspy.core.utcdatetime import UTCDateTime
import prov
import pandas as pd

# local imports
from gmprocess.stationtrace import StationTrace, TIMEFMT_MS
from gmprocess.stationstream import StationStream

TIMEPAT = '[0-9]{4}-[0-9]{2}-[0-9]{2}T'


class StreamWorkspace(object):
    def __init__(self, filename, exists=False):
        """Create an ASDF file given an Event and list of StationStreams.

        Args:
            filename (str): Path to ASDF file to create.
        """
        if not exists:
            compression = "gzip-3"
        else:
            compression = None
        self.dataset = pyasdf.ASDFDataSet(filename, compression=compression)

    @classmethod
    def open(cls, filename):
        """Load from existing ASDF file.
        """
        return cls(filename, exists=True)

    def close(self):
        # no close or other method for ASDF data sets?
        # this may force closing of the file...
        del self.dataset

    def __repr__(self):
        fmt = 'Events: %i Stations: %i Streams: %i'
        nevents = len(self.dataset.events)
        stations = []
        nstreams = 0
        for waveform in self.dataset.waveforms:
            inventory = waveform['StationXML']
            nstreams += len(waveform.get_waveform_tags())
            for station in inventory.networks[0].stations:
                stations.append(station.code)
        stations = set(stations)
        nstations = len(stations)
        return fmt % (nevents, nstations, nstreams)

    def addEvent(self, event):
        self.dataset.add_quakeml(event)

    def addStreams(self, event, streams, label=None):
        # to allow for multiple processed versions of the same Stream
        # let's keep a dictionary of stations and sequence number.
        eventid = get_id(event)
        if not self.hasEvent(eventid):
            self.addEvent(event)
        station_dict = {}
        for stream in streams:
            station = stream[0].stats['station']
            # is this a raw file? Check the trace for provenance info.
            is_raw = not len(stream[0].getProvenanceKeys())
            if is_raw:
                tag = 'raw_recording'
                level = 'raw'
            else:
                if label is not None:
                    tag = '%s_%s' % (station.lower(), label)
                else:
                    if station.lower() in station_dict:
                        station_sequence = station_dict[station.lower()] + 1
                    else:
                        station_sequence = 1
                    station_dict[station.lower()] = station_sequence
                    tag = '%s_%05i' % (station.lower(), station_sequence)
                level = 'processed'
            self.dataset.add_waveforms(stream, tag=tag, event_id=event)

            # add processing provenance info from streams
            if level == 'processed':
                provdocs = stream.getProvenanceDocuments()
                for provdoc in provdocs:
                    self.dataset.add_provenance_document(provdoc, name=tag)

            for trace in stream:
                path = '%s_%s' % (tag, trace.stats.channel)
                jdict = {}
                for key in trace.getParameterKeys():
                    value = trace.getParameter(key)
                    jdict[key] = value
                if len(jdict):
                    # NOTE: We would store this dictionary just as
                    # the parameters dictionary, but HDF cannot handle
                    # nested dictionaries.
                    # Also, this seems like a lot of effort
                    # just to store a string in HDF, but other
                    # approached failed. Suggestions are welcome.
                    jdict = stringify_dict(jdict)
                    jsonbytes = json.dumps(jdict).encode('utf-8')
                    jsonarray = np.frombuffer(jsonbytes, dtype=np.uint8)
                    dtype = 'ProcessingParameters'
                    self.dataset.add_auxiliary_data(jsonarray,
                                                    data_type=dtype,
                                                    path=path,
                                                    parameters={})
            inventory = stream.getInventory()
            self.dataset.add_stationxml(inventory)

    def getEventIds(self):
        idlist = []
        for event in self.dataset.events:
            eid = event.resource_id.id.replace('smi:local/', '')
            idlist.append(eid)
        return idlist

    def getStreamTags(self, eventid):
        """Get list of Stream "tags" which can be used to retrieve individual streams.
        """
        if not self.hasEvent(eventid):
            fmt = 'Event with a resource id containing %s could not be found.'
            raise KeyError(fmt % eventid)
        matching_tags = []
        for waveform in self.dataset.waveforms:
            tags = waveform.get_waveform_tags()
            for tag in tags:
                if eventid in waveform[tag][0].stats.asdf.event_ids:
                    matching_tags.append(tag)

        return matching_tags

    def getStreams(self, eventid, tags=None):
        """Get Stream from ASDF file given event id and input tags.

        Args:
            eventid (str):
                Event ID corresponding to an Event in the workspace.
            tags (list or None):
                List of stream tags to retrieve, or all if None.

        Returns:
            list: List of StationStream objects.
        """
        auxholder = []
        if 'ProcessingParameters' in self.dataset.auxiliary_data:
            auxholder = self.dataset.auxiliary_data.ProcessingParameters
        streams = []
        for waveform in self.dataset.waveforms:
            ttags = waveform.get_waveform_tags()
            if tags is None:
                wtags = ttags
            else:
                wtags = set(tags).intersection(set(ttags))
            for tag in wtags:
                if eventid in waveform[tag][0].stats.asdf.event_ids:
                    tstream = waveform[tag].copy()
                    inventory = waveform['StationXML']
                    traces = []
                    for ttrace in tstream:
                        trace = StationTrace(data=ttrace.data,
                                             header=ttrace.stats,
                                             inventory=inventory)
                        if tag in self.dataset.provenance.list():
                            provdoc = self.dataset.provenance[tag]
                            trace.setProvenanceDocument(provdoc)
                        trace_path = '%s_%s' % (tag, trace.stats.channel)
                        if trace_path in auxholder:
                            bytelist = auxholder[trace_path].data[:].tolist()
                            jsonstr = ''.join([chr(b) for b in bytelist])
                            jdict = json.loads(jsonstr)
                            # jdict = unstringify_dict(jdict)
                            for key, value in jdict.items():
                                trace.setParameter(key, value)

                        traces.append(trace)
                    stream = StationStream(traces=traces)
                    streams.append(stream)
        return streams

    def getStations(self):
        """Get list of station codes that can be used to uniquely identify
        a station within the file.
        """
        pass

    def addStationMetrics(self, station_code, dict_or_metric_xml):
        """Add station metrics IMC/IMT information to ASDF file. Input
        can either be a dict (?) or pre-defined XML file. XML
        data will be written to ASDF file.
        """
        pass

    def getStationMetrics(self, station_code):
        """Retrieve station metrics given station code.
        """
        pass

    def setStreamMetrics(self, stream_tag, station_summary_or_metric_xml):
        """Add station metrics IMC / IMT information to ASDF file. Input
        can either be a dict(?) or pre - defined XML file. XML
        data will be written to ASDF file.
        """
        pass

    def getProvenance(self, stream_tag):
        """Return data structure (?) containing processing history for a stream.
        """
        pass

    def summarizeLabels(self):
        # return a table with columns of:
        # label - see addStreams() method. Labels default to '00001', etc.
        # num_streams - Number of streams with that label
        # user id - System user name (jsmith, etc.)
        # user name - Full name of user (Jane Smith) - optional
        # user email - Email address of user
        # software - Name of software used to process data
        # version - Version of software used to process data
        provtags = self.dataset.provenance.list()
        cols = ['Label', 'UserID', 'UserName',
                'UserEmail', 'Software', 'Version']
        df = pd.DataFrame(columns=cols, index=None)
        labels = list(set([ptag.split('_')[1] for ptag in provtags]))
        labeldict = {}
        for label in labels:
            for ptag in provtags:
                if label in ptag:
                    labeldict[label] = ptag
        for label, ptag in labeldict.items():
            row = pd.Series(index=cols)
            row['Label'] = label
            provdoc = self.dataset.provenance[ptag]
            user, software = get_agents(provdoc)
            row['UserID'] = user['id']
            row['UserName'] = user['name']
            row['UserEmail'] = user['email']
            row['Software'] = software['name']
            row['Version'] = software['version']
            df = df.append(row, ignore_index=True)

        return df

    def getInventory(self, eventid):
        """Get an Obspy Inventory object from the ASDF file.
        """

    def hasEvent(self, eventid):
        for event in self.dataset.events:
            if event.resource_id.id.find(eventid) > -1:
                return True
        return False

    def getEvent(self, eventid):
        """Get an Obspy Event object from the ASDF file.
        """
        eventobj = None
        for event in self.dataset.events:
            if event.resource_id.id.find(eventid) > -1:
                eventobj = event
                break
        if eventobj is None:
            fmt = 'Event with a resource id containing %s could not be found.'
            raise KeyError(fmt % eventid)
        return eventobj


def stringify_dict(indict):
    for key, value in indict.items():
        if isinstance(value, UTCDateTime):
            indict[key] = value.strftime(TIMEFMT_MS)
        elif isinstance(value, dict):
            indict[key] = stringify_dict(value)
    return indict


def unstringify_dict(indict):
    for key, value in indict.items():
        if isinstance(value, str) and re.match(TIMEPAT, value):
            indict[key] = UTCDateTime(value)
        elif isinstance(value, dict):
            indict[key] = unstringify_dict(value)
    return indict


def get_id(event):
    eid = event.resource_id.id.replace('smi:local/', '')
    return eid


def get_agents(provdoc):
    software = {}
    person = {}
    jdict = json.loads(provdoc.serialize())
    for key, value in jdict['agent'].items():
        is_person = re.search('sp[0-9]{3}_pp', key) is not None
        is_software = re.search('sp[0-9]{3}_sa', key) is not None
        if is_person:
            person['id'] = value['prov:label']
            if 'seis_prov:email' in value:
                person['email'] = value['seis_prov:email']
            if 'seis_prov:name' in value:
                person['name'] = value['seis_prov:name']
        elif is_software:
            software['name'] = value['seis_prov:software_name']
            software['version'] = value['seis_prov:software_version']
        else:
            pass

    return (person, software)
