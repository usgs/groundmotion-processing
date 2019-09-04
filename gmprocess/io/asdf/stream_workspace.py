# stdlib imports
import json
import re
import copy
import warnings
import logging
import os

# third party imports
import pyasdf
import numpy as np
from obspy.core.utcdatetime import UTCDateTime
import pandas as pd
from h5py.h5py_warnings import H5pyDeprecationWarning
from obspy.geodetics.base import gps2dist_azimuth
from openquake.hazardlib.geo.geodetic import distance

# local imports
from gmprocess.stationtrace import StationTrace, TIMEFMT_MS
from gmprocess.stationstream import StationStream
from gmprocess.streamcollection import StreamCollection
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.exception import GMProcessException
from gmprocess.event import ScalarEvent

TIMEPAT = '[0-9]{4}-[0-9]{2}-[0-9]{2}T'
EVENT_TABLE_COLUMNS = ['id', 'time', 'latitude',
                       'longitude', 'depth', 'magnitude', 'magnitude_type']
NON_IMT_COLUMNS = ['ELEVATION', 'EPICENTRAL_DISTANCE',
                   'HYPOCENTRAL_DISTANCE', 'LAT', 'LON',
                   'NAME', 'NETID', 'SOURCE', 'STATION']
FLATFILE_COLUMNS = ['EarthquakeId', 'EarthquakeTime', 'EarthquakeLatitude',
                    'EarthquakeLongitude', 'EarthquakeDepth',
                    'EarthquakeMagnitude', 'EarthquakeMagnitudeType',
                    'Network', 'NetworkDescription',
                    'StationCode', 'StationID',
                    'StationDescription',
                    'StationLatitude', 'StationLongitude',
                    'StationElevation', 'SamplingRate',
                    'EpicentralDistance', 'HypocentralDistance',
                    'H1Lowpass', 'H1Highpass',
                    'H2Lowpass', 'H2Highpass', 'SourceFile']

M_PER_KM = 1000

FORMAT_VERSION = '1.0'


class StreamWorkspace(object):
    def __init__(self, filename, compression=None):
        """Create an ASDF file given an Event and list of StationStreams.

        Args:
            filename (str):
                Path to ASDF file to create.
            compression (str):
                Any value supported by pyasdf.asdf_data_set.ASDFDataSet.
        """
        if os.path.exists(filename):
            self.dataset = pyasdf.ASDFDataSet(filename)
        else:
            self.dataset = pyasdf.ASDFDataSet(
                filename, compression=compression)
        self.FORMAT_VERSION = FORMAT_VERSION

    @classmethod
    def create(cls, filename, compression=None):
        """Load from existing ASDF file.

        Args:
            filename (str):
                Path to existing ASDF file.
            compression (str):
                Any value supported by pyasdf.asdf_data_set.ASDFDataSet.

        Returns:
            StreamWorkspace: Object containing ASDF file.
        """
        if os.path.exists(filename):
            raise IOError('File %s already exists.' % filename)
        return cls(filename)

    @classmethod
    def open(cls, filename):
        """Load from existing ASDF file.

        Args:
            filename (str):
                Path to existing ASDF file.

        Returns:
            StreamWorkspace: Object containing ASDF file.
        """
        if not os.path.exists(filename):
            raise IOError('File %s does not exist.' % filename)
        return cls(filename)

    def __repr__(self):
        """Provide summary string representation of the file.

        Returns:
            str: Summary string representation of the file.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore",
                                  category=H5pyDeprecationWarning)
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
        """Add event object to file.

        Args:
            event (Event): Obspy event object.
        """
        self.dataset.add_quakeml(event)

    def addStreams(self, event, streams, label=None):
        """Add a sequence of StationStream objects to an ASDF file.

        Args:
            event (Event):
                Obspy event object.
            streams (list):
                List of StationStream objects.
            label (str):
                Label to attach to stream sequence. Cannot contain an
                underscore.
        """
        if label is not None:
            if '_' in label:
                raise GMProcessException(
                    'Stream label cannot contain an underscore.')

        # To allow for multiple processed versions of the same Stream
        # let's keep a dictionary of stations and sequence number.
        eventid = _get_id(event)
        if not self.hasEvent(eventid):
            self.addEvent(event)

        for stream in streams:
            station = stream[0].stats['station']
            logging.info('Adding waveforms for station %s' % station)
            # is this a raw file? Check the trace for provenance info.
            is_raw = not len(stream[0].getProvenanceKeys())

            if label is None:
                tfmt = '%Y%m%d%H%M%S'
                tnow = UTCDateTime.now().strftime(tfmt)
                label = 'processed%s' % tnow
            tag = '%s_%s' % (eventid, label)
            if is_raw:
                level = 'raw'
            else:
                level = 'processed'
            self.dataset.add_waveforms(stream, tag=tag, event_id=event)

            # add processing provenance info from traces
            if level == 'processed':
                provdocs = stream.getProvenanceDocuments()
                for provdoc, trace in zip(provdocs, stream):
                    provfmt = '%s_%s_%s_%s_%s'
                    net = trace.stats.network.lower()
                    sta = trace.stats.station.lower()
                    loc = trace.stats.location.lower()
                    if loc == '--':
                        loc = ''
                    cha = trace.stats.channel.lower()
                    provtpl = (net, sta, loc, cha, tag)
                    provname = provfmt % provtpl
                    self.dataset.add_provenance_document(
                        provdoc,
                        name=provname
                    )

            # add processing parameters from streams
            jdict = {}
            for key in stream.getStreamParamKeys():
                value = stream.getStreamParam(key)
                jdict[key] = value

            if len(jdict):
                # NOTE: We would store this dictionary just as
                # the parameters dictionary, but HDF cannot handle
                # nested dictionaries.
                # Also, this seems like a lot of effort
                # just to store a string in HDF, but other
                # approached failed. Suggestions are welcome.
                jdict = _stringify_dict(jdict)
                jsonbytes = json.dumps(jdict).encode('utf-8')
                jsonarray = np.frombuffer(jsonbytes, dtype=np.uint8)
                dtype = 'StreamProcessingParameters'
                paramfmt = '%s_%s/%s_%s_%s_%s_%s'
                net = stream[0].stats.network.lower()
                sta = stream[0].stats.station.lower()
                loc = stream[0].stats.location.lower()
                if loc == '--':
                    loc = ''
                inst = stream.get_id().lower().split('.')[2]
                paramtpl = (net, sta, net, sta, loc, inst, tag)
                parampath = paramfmt % paramtpl
                self.dataset.add_auxiliary_data(
                    jsonarray,
                    data_type=dtype,
                    path=parampath,
                    parameters={}
                )

            # add processing parameters from traces
            for trace in stream:
                procfmt = '%s_%s/%s_%s_%s_%s_%s'
                net = trace.stats.network.lower()
                sta = trace.stats.station.lower()
                loc = trace.stats.location.lower()
                if loc == '--':
                    loc = ''
                cha = trace.stats.channel.lower()
                proctpl = (net, sta, net, sta, loc, cha, tag)
                procname = procfmt % proctpl
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
                    jdict = _stringify_dict(jdict)
                    jsonbytes = json.dumps(jdict).encode('utf-8')
                    jsonarray = np.frombuffer(jsonbytes, dtype=np.uint8)
                    dtype = 'TraceProcessingParameters'
                    self.dataset.add_auxiliary_data(
                        jsonarray,
                        data_type=dtype,
                        path=procname,
                        parameters={}
                    )

                # some processing metadata can consist of arrays that are as
                # big as or larger, so these should be saved as numpy arrays
                # in the HDF, not as JSON-ized versions of the arrays as
                # Trace processing parameters are.
                for specname in trace.getAuxArrayNames():
                    spectrum = trace.getAuxArray(specname)
                    # we expect many of these specnames to
                    # be joined with underscores.
                    name_parts = specname.split('_')
                    base_dtype = ''.join([part.capitalize()
                                          for part in name_parts])
                    for array_name, array in spectrum.items():
                        dtype = 'Array' + base_dtype + array_name.capitalize()
                        try:
                            self.dataset.add_auxiliary_data(
                                array,
                                data_type=dtype,
                                path=procname,
                                parameters={}
                            )
                        except Exception as e:
                            x = 1
            inventory = stream.getInventory()
            self.dataset.add_stationxml(inventory)

    def getEventIds(self):
        """Return list of event IDs for events in ASDF file.

        Returns:
            list: List of eventid strings.
        """
        idlist = []
        for event in self.dataset.events:
            eid = event.resource_id.id.replace('smi:local/', '')
            idlist.append(eid)
        return idlist

    def getLabels(self):
        """Return all of the processing labels.

        Returns:
            list: List of processing labels.
        """
        all_tags = []
        for w in self.dataset.waveforms:
            all_tags.extend(w.get_waveform_tags())
        all_labels = list(set([at.split('_')[1] for at in all_tags]))
        labels = list(set(all_labels))
        return labels

    def getStreams(self, eventid, stations=None, labels=None):
        """Get Stream from ASDF file given event id and input tags.

        Args:
            eventid (str):
                Event ID corresponding to an Event in the workspace.
            stations (list):
                List of stations to search for.
            labels (list):
                List of processing labels to search for.

        Returns:
            StreamCollection: Object containing list of organized
            StationStreams.
        """
        trace_auxholder = []
        stream_auxholder = []
        if 'TraceProcessingParameters' in self.dataset.auxiliary_data:
            trace_auxholder = self.dataset.auxiliary_data.TraceProcessingParameters
        if 'StreamProcessingParameters' in self.dataset.auxiliary_data:
            stream_auxholder = self.dataset.auxiliary_data.StreamProcessingParameters
        streams = []

        if stations is None:
            stations = self.getStations(eventid)
        if labels is None:
            labels = self.getLabels()

        # tried doing a query here using dataset ifilter on event,
        # but it didn't work...
        for waveform in self.dataset.waveforms:
            tags = waveform.get_waveform_tags()
            for tag in tags:
                teventid, tlabel = tag.split('_')
                if eventid != teventid:
                    continue
                if tlabel not in labels:
                    continue
                stream_name = list(
                    waveform.get_waveform_attributes().keys())[0]
                parts = stream_name.split('.')
                tstation = parts[1]
                if tstation not in stations:
                    continue

                tstream = waveform[tag]

                inventory = waveform['StationXML']
                for ttrace in tstream:
                    trace = StationTrace(data=ttrace.data,
                                         header=ttrace.stats,
                                         inventory=inventory)
                    net = trace.stats.network.lower()
                    sta = trace.stats.station.lower()
                    cha = trace.stats.channel.lower()
                    loc = trace.stats.location.lower()

                    if loc == '--':
                        loc = ''

                    # get the provenance information
                    provfmt = '%s_%s_%s_%s_%s'
                    provtpl = (net, sta, loc, cha, tag)
                    provname = provfmt % provtpl
                    if provname in self.dataset.provenance.list():
                        provdoc = self.dataset.provenance[provname]
                        trace.setProvenanceDocument(provdoc)

                    # get the trace processing parameters
                    trace_fmt = '%s_%s_%s_%s_%s'
                    top = '%s_%s' % (net, sta)
                    trace_tpl = (net, sta, loc, cha, tag)
                    trace_path = trace_fmt % trace_tpl
                    if top in trace_auxholder:
                        root_auxholder = trace_auxholder[top]
                        if trace_path in root_auxholder:
                            bytelist = root_auxholder[
                                trace_path].data[:].tolist()
                            jsonstr = ''.join([chr(b) for b in bytelist])
                            jdict = json.loads(jsonstr)
                            for key, value in jdict.items():
                                trace.setParameter(key, value)

                    # get the trace spectra arrays from auxiliary,
                    # repack into stationtrace object
                    spectra = {}
                    for aux in self.dataset.auxiliary_data.list():
                        if aux.startswith('Array'):
                            auxarray = self.dataset.auxiliary_data[aux]
                            if top not in auxarray.list():
                                continue
                            auxarray_top = auxarray[top]
                            if trace_path in auxarray_top:
                                specparts = camel_case_split(aux)
                                array_name = specparts[-1].lower()
                                specname = '_'.join(specparts[2:-1]).lower()
                                specarray = auxarray_top[trace_path].data.value
                                if specname in spectra:
                                    spectra[specname][array_name] = specarray
                                else:
                                    spectra[specname] = {array_name: specarray}
                    for key, value in spectra.items():
                        trace.setAuxArray(key, value)

                    stream = StationStream(traces=[trace])
                    stream.tag = tag  # testing this out

                    # get the stream processing parameters
                    inst = stream.get_id().lower().split('.')[2]
                    stream_fmt = '%s_%s_%s_%s_%s'
                    stream_tpl = (net, sta, loc, inst, tag)
                    stream_path = stream_fmt % stream_tpl
                    if top in stream_auxholder:
                        top_auxholder = stream_auxholder[top]
                        if stream_path in top_auxholder:
                            auxarray = top_auxholder[stream_path]
                            bytelist = auxarray.data[:].tolist()
                            jsonstr = ''.join([chr(b) for b in bytelist])
                            jdict = json.loads(jsonstr)
                            for key, value in jdict.items():
                                stream.setStreamParam(key, value)

                    streams.append(stream)
        streams = StreamCollection(streams)
        return streams

    def getStations(self, eventid=None):
        """Get list of station codes within the file.

        Args:
            eventid (str):
                Event ID corresponding to an Event in the workspace.

        Returns:
            list: List of station codes contained in workspace.
        """
        stations = []
        for waveform in self.dataset.waveforms:
            for stream_name, _ in waveform.get_waveform_attributes().items():
                parts = stream_name.split('.')
                station = parts[1]
                if station in stations:
                    continue
                stations.append(station)
        return stations

    def insert_aux(self, datastr, data_name, path):
        """Insert a string (usually json or xml) into Auxilliary array.

        Args:
            datastr (str): String containing data to insert into Aux array.
            data_name (str): What this data should be called in the ASDF file.
            path (str): The aux path where this data should be stored.
        """
        # this seems like a lot of effort
        # just to store a string in HDF, but other
        # approached failed. Suggestions are welcome.
        databuf = datastr.encode('utf-8')
        data_array = np.frombuffer(databuf, dtype=np.uint8)
        dtype = data_name
        self.dataset.add_auxiliary_data(
            data_array,
            data_type=dtype,
            path=path,
            parameters={}
        )

    def calcStationMetrics(self, eventid, stations=None, labels=None):
        """Calculate distance measures for each station.

        Args:
            eventid (str):
                ID of event to search for in ASDF file.
            stations (list):
                List of stations to create metrics for.
            labels (list):
                List of processing labels to create metrics for.
        """
        if not self.hasEvent(eventid):
            fmt = 'No event matching %s found in workspace.'
            raise KeyError(fmt % eventid)

        streams = self.getStreams(eventid, stations=stations, labels=labels)
        event = self.getEvent(eventid)
        for stream in streams:
            tag = stream.tag
            _, label = tag.split('_')
            elat = event.latitude
            elon = event.longitude
            edepth = event.depth_km
            slat = stream[0].stats.coordinates.latitude
            slon = stream[0].stats.coordinates.longitude
            sdep = stream[0].stats.coordinates.elevation
            epidist_m, _, _ = gps2dist_azimuth(elat, elon, slat, slon)
            hypocentral_distance = distance(elon, elat, edepth,
                                            slon, slat, -sdep / M_PER_KM)
            xmlfmt = '''<station_metrics>
            <hypocentral_distance units="km">%.1f</hypocentral_distance>
            <epicentral_distance units="km">%.1f</epicentral_distance>
            </station_metrics>
            '''
            xmlstr = xmlfmt % (hypocentral_distance, epidist_m / M_PER_KM)

            metricfmt = '%s_%s/%s_%s_%s_%s_%s'
            net = stream[0].stats.network.lower()
            sta = stream[0].stats.station.lower()
            loc = stream[0].stats.location.lower()
            if loc == '--':
                loc = ''
            inst = stream.get_id().lower().split('.')[2]
            metrictpl = (net, sta, net, sta, loc, inst, eventid)
            metricpath = metricfmt % metrictpl

            self.insert_aux(xmlstr, 'StationMetrics', metricpath)

    def calcMetrics(self, eventid, stations=None, labels=None, config=None):
        """Calculate both stream and station metrics for a set of waveforms.

        Args:
            eventid (str):
                ID of event to search for in ASDF file.
            stations (list):
                List of stations to create metrics for.
            labels (list):
                List of processing labels to create metrics for.
            config (dict): Configuration dictionary.
        """
        self.calcStreamMetrics(eventid,
                               stations=stations,
                               labels=labels, config=config)
        self.calcStationMetrics(eventid, stations=stations, labels=labels)

    def calcStreamMetrics(self, eventid, stations=None,
                          labels=None, config=None):
        """Create station metrics for specified event/streams.

        Args:
            eventid (str):
                ID of event to search for in ASDF file.
            stations (list):
                List of stations to create metrics for.
            labels (list):
                List of processing labels to create metrics for.
            imclist (list):
                List of valid component names.
            imtlist (list):
                List of valid IMT names.
            config (dict):
                Config dictionary.
        """
        if not self.hasEvent(eventid):
            fmt = 'No event matching %s found in workspace.'
            raise KeyError(fmt % eventid)

        streams = self.getStreams(eventid, stations=stations, labels=labels)
        event = self.getEvent(eventid)
        for stream in streams:
            tag = stream.tag
            instrument = stream.get_id()
            eventid, label = tag.split('_')
            if label not in labels:
                continue
            try:
                summary = StationSummary.from_config(
                    stream, event=event, config=config)
            except Exception as pgme:
                fmt = ('Could not create stream metrics for event %s,'
                       'instrument %s: "%s"')
                logging.warning(fmt % (eventid, instrument, str(pgme)))
                continue

            xmlstr = summary.get_metric_xml()

            metricfmt = '%s_%s/%s_%s_%s_%s_%s'
            net = stream[0].stats.network.lower()
            sta = stream[0].stats.station.lower()
            loc = stream[0].stats.location.lower()
            if loc == '--':
                loc = ''
            inst = stream.get_id().lower().split('.')[2]
            metrictpl = (net, sta, net, sta, loc, inst, tag)
            metricpath = metricfmt % metrictpl

            # this seems like a lot of effort
            # just to store a string in HDF, but other
            # approached failed. Suggestions are welcome.
            xmlbytes = xmlstr.encode('utf-8')
            jsonarray = np.frombuffer(xmlbytes, dtype=np.uint8)
            dtype = 'WaveFormMetrics'

            self.dataset.add_auxiliary_data(
                jsonarray,
                data_type=dtype,
                path=metricpath,
                parameters={}
            )

    def getTables(self, label, config=None):
        '''Retrieve dataframes containing event information and IMC/IMT metrics.

        Args:
            label (str): Calculate metrics only for the given label.
            config (dict): Config dictionary.

        Returns:
            tuple: Elements are:
                   - pandas DataFrame containing event information:
                     - id Event ID
                     - time Time of origin
                     - latitude Latitude of origin
                     - longitude Longitude of origin
                     - depth Depth of origin (km)
                     - magnitude Magnitude at origin (km)
                     - magnitude_type Magnitude type at origin
                   - dictionary of DataFrames, where keys are IMCs and
                     values are DataFrames with columns:
                     - EarthquakeId Earthquake id from event table
                     - Network Network code
                     - StationCode Station code
                     - StationDescription Long form description of station
                       location (may be blank)
                     - StationLatitude Station latitude
                     - StationLongitude Station longitude
                     - StationElevation Station elevation
                     - SamplingRate Data sampling rate in Hz
                     - EpicentralDistance Distance from origin epicenter
                       (surface) to station
                     - HypocentralDistance Distance from origin hypocenter
                       (depth) to station
                     - HN1Lowpass Low pass filter corner frequency for first
                       horizontal channel
                     - HN1Highpass High pass filter corner frequency for first
                       horizontal channel
                     - HN2Lowpass Low pass filter corner frequency for second
                       horizontal channel
                     - HN2Highpass High pass filter corner frequency for
                       second horizontal channel
                     - ...desired IMTs (PGA, PGV, SA(0.3), etc.)
        '''
        event_table = pd.DataFrame(columns=EVENT_TABLE_COLUMNS)
        imc_tables = {}
        for eventid in self.getEventIds():
            event = self.getEvent(eventid)
            edict = {
                'id': event.id,
                'time': event.time,
                'latitude': event.latitude,
                'longitude': event.longitude,
                'depth': event.depth_km,
                'magnitude': event.magnitude,
                'magnitude_type': event.magnitude_type
            }
            event_table = event_table.append(edict, ignore_index=True)
            streams = self.getStreams(eventid, labels=[label])
            for stream in streams:
                if not stream.passed:
                    continue
                if config is None:
                    station = stream[0].stats.station
                    summary = self.getStreamMetrics(eventid, station, label)
                else:
                    summary = StationSummary.from_config(
                        stream, event=event, config=config)

                if summary is None:
                    continue

                imclist = summary.pgms['IMC'].unique().tolist()
                imtlist = summary.pgms['IMT'].unique().tolist()
                imtlist.sort(key=_natural_keys)

                for imc in imclist:
                    if imc not in imc_tables:
                        cols = FLATFILE_COLUMNS + imtlist
                        imc_table = pd.DataFrame(columns=cols)
                        row = _get_table_row(stream, summary, event, imc)
                        if not len(row):
                            continue
                        imc_table = imc_table.append(row, ignore_index=True)
                        imc_tables[imc] = imc_table
                    else:
                        imc_table = imc_tables[imc]
                        row = _get_table_row(stream, summary, event, imc)
                        if not len(row):
                            continue
                        imc_table = imc_table.append(row, ignore_index=True)
                        imc_tables[imc] = imc_table

        # Remove any empty IMT columns from the IMC tables
        for key, table in imc_tables.items():
            for col in table.columns:
                if table[col].dropna().empty:
                    table.drop(columns=col, inplace=True)
            imc_tables[key] = table

        return (event_table, imc_tables)

    def getStreamMetrics(self, eventid, station, label):
        """Extract a StationSummary object from the ASDF file for a given input Stream.

        Args:
            eventid (str):
                ID of event to search for in ASDF file.
            station (str):
                Station to return metrics from.
            label (str):
                Processing label to return metrics from.

        Returns:
            StationSummary: Object containing all stream metrics or None.
        """
        if 'WaveFormMetrics' not in self.dataset.auxiliary_data:
            logging.warning('Waveform metrics not found in workspace, '
                            'cannot get stream metrics.')
        auxholder = self.dataset.auxiliary_data.WaveFormMetrics

        # get the stream matching the eventid, station, and label
        streams = self.getStreams(eventid, stations=[station],
                                  labels=[label])
        if not len(streams):
            fmt = '''Stream matching event ID %s,
            station ID %s, and processing label %s not found in workspace.'''
            msg = fmt % (eventid, station, label)
            logging.warning(msg)
            return None

        metricfmt = '%s_%s_%s_%s_%s'
        net = streams[0][0].stats.network.lower()
        sta = streams[0][0].stats.station.lower()
        loc = streams[0][0].stats.location.lower()
        if loc == '--':
            loc = ''
        tag = streams[0].tag
        inst = streams[0].get_id().lower().split('.')[2]
        metrictpl = (net, sta, loc, inst, tag)
        metricpath = metricfmt % metrictpl
        top = '%s_%s' % (net, sta)
        if top in auxholder:
            tauxholder = auxholder[top]
            if metricpath not in tauxholder:
                fmt = 'Stream metrics path (%s) not in WaveFormMetrics auxiliary_data.'
                logging.warning(fmt % metricpath)
                return None

            bytelist = tauxholder[metricpath].data[:].tolist()
            xml_stream = ''.join([chr(b) for b in bytelist])
            xml_stream = xml_stream.encode('utf-8')

        if 'StationMetrics' not in self.dataset.auxiliary_data:
            raise KeyError('Station metrics not found in workspace.')
        auxholder = self.dataset.auxiliary_data.StationMetrics
        inst = streams[0].get_id().lower().split('.')[2]
        station_fmt = '%s_%s_%s_%s_%s'
        station_tpl = (net, sta, loc, inst, eventid)
        station_path = station_fmt % station_tpl
        if top in auxholder:
            tauxholder = auxholder[top]
            if station_path not in tauxholder:
                logging.warning(
                    'Stream path (%s) not in StationMetrics auxiliary_data.'
                    % station_path)
                return

            bytelist = tauxholder[station_path].data[:].tolist()
            xml_station = ''.join([chr(b) for b in bytelist])
            xml_station = xml_station.encode('utf-8')

        summary = StationSummary.from_xml(xml_stream, xml_station)
        return summary

    def summarizeLabels(self):
        """
        Summarize the processing metadata associated with each label in the
        file.

        Returns:
            DataFrame:
                Pandas DataFrame with columns:
                    - Label Processing label.
                    - UserID user id (i.e., jsmith)
                    - UserName Full user name (i.e., Jane Smith) (optional)
                    - UserEmail Email adress (i.e., jsmith@awesome.org)
                      (optional)
                    - Software Name of processing software (i.e., gmprocess)
                    - Version Version of software (i.e., 1.4)

        """
        provtags = self.dataset.provenance.list()
        cols = ['Label', 'UserID', 'UserName',
                'UserEmail', 'Software', 'Version']
        df = pd.DataFrame(columns=cols, index=None)
        labels = list(set([ptag.split('_')[5] for ptag in provtags]))
        labeldict = {}
        for label in labels:
            for ptag in provtags:
                if label in ptag:
                    labeldict[label] = ptag
        for label, ptag in labeldict.items():
            row = pd.Series(index=cols)
            row['Label'] = label
            provdoc = self.dataset.provenance[ptag]
            user, software = _get_agents(provdoc)
            row['UserID'] = user['id']
            row['UserName'] = user['name']
            row['UserEmail'] = user['email']
            row['Software'] = software['name']
            row['Version'] = software['version']
            df = df.append(row, ignore_index=True)

        return df

    def getInventory(self, eventid):
        """Get an Obspy Inventory object from the ASDF file.

        Args:
            eventid (str): ID of event to search for in ASDF file.

        Returns:
            Inventory: Obspy inventory object capturing all of the
                       networks, stations, and channels contained in file.
        """
        inventory = None
        for waveform in self.dataset.waveforms:
            tinv = waveform.StationXML
            if inventory is None:
                inventory = tinv
            else:
                net1 = inventory.networks[0]
                net2 = tinv.networks[0]
                if net1.code == net2.code:
                    net1.stations.append(copy.deepcopy(net2.stations[0]))
                else:
                    inventory.networks.append(copy.deepcopy(net2))

        return inventory

    def hasEvent(self, eventid):
        """Verify that the workspace file contains an event matching eventid.

        Args:
            eventid (str): ID of event to search for in ASDF file.

        Returns:
            bool: True if event matching ID is found, False if not.
        """
        for event in self.dataset.events:
            if event.resource_id.id.find(eventid) > -1:
                return True
        return False

    def getEvent(self, eventid):
        """Get a ScalarEvent object from the ASDF file.

        Args:
            eventid (str): ID of event to search for in ASDF file.

        Returns:
            ScalarEvent:
                Flattened version of Obspy Event object.
        """
        eventobj = None
        for event in self.dataset.events:
            if event.resource_id.id.find(eventid) > -1:
                eventobj = event
                break
        if eventobj is None:
            fmt = 'Event with a resource id containing %s could not be found.'
            raise KeyError(fmt % eventid)
        eventobj2 = ScalarEvent.fromEvent(eventobj)
        return eventobj2

    def getProvenance(self, eventid, stations=None, labels=None):
        """Return DataFrame with processing history for streams matching input criteria.

        Output will look like this:
          Record  Processing Step     Step Attribute              Attribute Value
0    NZ.HSES.HN1  Remove Response        input_units                       counts
1    NZ.HSES.HN1  Remove Response       output_units                       cm/s^2
2    NZ.HSES.HN1          Detrend  detrending_method                       linear
3    NZ.HSES.HN1          Detrend  detrending_method                       demean
4    NZ.HSES.HN1              Cut       new_end_time  2016-11-13T11:05:44.000000Z
5    NZ.HSES.HN1              Cut     new_start_time  2016-11-13T11:02:58.000000Z
6    NZ.HSES.HN1            Taper               side                         both
7    NZ.HSES.HN1            Taper        taper_width                         0.05
8    NZ.HSES.HN1            Taper        window_type                         Hann
...

        Args:
            eventid (str):
                Event ID corresponding to an Event in the workspace.
            stations (list):
                List of stations to search for.
            labels (list):
                List of processing labels to search for.

        Returns:
            DataFrame:
                Table of processing steps/parameters (see above).

        """
        if stations is None:
            stations = self.getStations(eventid)
        if labels is None:
            labels = self.getLabels()
        cols = ['Record', 'Processing Step',
                'Step Attribute', 'Attribute Value']
        df = pd.DataFrame(columns=cols)
        for provname in self.dataset.provenance.list():
            has_station = False
            for station in stations:
                if station.lower() in provname:
                    has_station = True
                    break
            has_label = False
            for label in labels:
                if label.lower() in provname:
                    has_label = True
                    break
            if not has_label or not has_station:
                continue

            provdoc = self.dataset.provenance[provname]
            serial = json.loads(provdoc.serialize())
            for activity, attrs in serial['activity'].items():
                pstep = None
                for key, value in attrs.items():
                    if key == 'prov:label':
                        pstep = value
                        continue
                    if key == 'prov:type':
                        continue
                    if not isinstance(value, str):
                        if value['type'] == 'xsd:dateTime':
                            value = UTCDateTime(value['$'])
                        elif value['type'] == 'xsd:double':
                            value = float(value['$'])
                        elif value['type'] == 'xsd:int':
                            value = int(value['$'])
                        else:
                            pass
                    attrkey = key.replace('seis_prov:', '')
                    row = pd.Series(index=cols)
                    row['Record'] = provname
                    row['Processing Step'] = pstep
                    row['Step Attribute'] = attrkey
                    row['Attribute Value'] = value
                    df = df.append(row, ignore_index=True)

        return df


def _stringify_dict(indict):
    for key, value in indict.items():
        if isinstance(value, UTCDateTime):
            indict[key] = value.strftime(TIMEFMT_MS)
        elif isinstance(value, dict):
            indict[key] = _stringify_dict(value)
    return indict


def _get_id(event):
    eid = event.origins[0].resource_id.id

    return eid


def _get_agents(provdoc):
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

    if 'name' not in person:
        person['name'] = ''
    if 'email' not in person:
        person['email'] = ''
    return (person, software)


def _get_table_row(stream, summary, event, imc):

    h1 = stream.select(channel='*1')
    h2 = stream.select(channel='*2')
    if not len(h1):
        h1 = stream.select(channel='*N')
        h2 = stream.select(channel='*E')

    if not len(h1) or not len(h2):
        return {}
    h1 = h1[0]
    h2 = h2[0]

    h1_lowfilt = h1.getProvenance('lowpass_filter')
    h1_highfilt = h1.getProvenance('highpass_filter')
    h1_lowpass = np.nan
    h1_highpass = np.nan
    if len(h1_lowfilt):
        h1_lowpass = h1_lowfilt[0]['corner_frequency']
    if len(h1_highfilt):
        h1_highpass = h1_highfilt[0]['corner_frequency']

    h2_lowfilt = h2.getProvenance('lowpass_filter')
    h2_highfilt = h2.getProvenance('highpass_filter')
    h2_lowpass = np.nan
    h2_highpass = np.nan
    if len(h2_lowfilt):
        h2_lowpass = h2_lowfilt[0]['corner_frequency']
    if len(h2_highfilt):
        h2_highpass = h2_highfilt[0]['corner_frequency']

    row = {'EarthquakeId': event.id,
           'EarthquakeTime': event.time,
           'EarthquakeLatitude': event.latitude,
           'EarthquakeLongitude': event.longitude,
           'EarthquakeDepth': event.depth_km,
           'EarthquakeMagnitude': event.magnitude,
           'EarthquakeMagnitudeType': event.magnitude_type,
           'Network': stream[0].stats.network,
           'NetworkDescription': stream[0].stats.standard.source,
           'StationCode': stream[0].stats.station,
           'StationID': stream.get_id(),
           'StationDescription': stream[0].stats.standard.station_name,
           'StationLatitude': stream[0].stats.coordinates.latitude,
           'StationLongitude': stream[0].stats.coordinates.longitude,
           'StationElevation': stream[0].stats.coordinates.elevation,
           'SamplingRate': stream[0].stats.sampling_rate,
           'EpicentralDistance': summary.epicentral_distance,
           'HypocentralDistance': summary.hypocentral_distance,
           'H1Lowpass': h1_lowpass,
           'H1Highpass': h1_highpass,
           'H2Lowpass': h2_lowpass,
           'H2Highpass': h2_highpass,
           'SourceFile': stream[0].stats.standard.source_file}
    imt_frame = summary.pgms[summary.pgms['IMC'] == imc].drop('IMC', axis=1)
    imts = dict(zip(imt_frame['IMT'], imt_frame['Result']))
    row.update(imts)
    return row


def _natural_keys(text):
    """
    Helper function for sorting IMT list. This is needed because using the
    plain .sort() will put SA(10.0) before SA(2.0), for example.
    """
    return [_atof(c) for c in re.split(
        r'[+-]?([0-9]+(?:[.][0-9]*)?|[.][0-9]+)', text)]


def _atof(text):
    try:
        retval = float(text)
    except ValueError:
        retval = text
    return retval


def camel_case_split(identifier):
    matches = re.finditer(
        '.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]
