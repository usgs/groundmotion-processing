# stdlib imports
import json
import re
import copy
import warnings
import logging
import os
#kyle test comment#
# third party imports
import pyasdf
import prov.model
import numpy as np
from obspy.core.utcdatetime import UTCDateTime
import pandas as pd
from h5py.h5py_warnings import H5pyDeprecationWarning
from impactutils.rupture.factory import get_rupture
from impactutils.rupture.origin import Origin
from mapio.gmt import GMTGrid

# local imports
from gmprocess.stationtrace import (StationTrace, TIMEFMT_MS, NS_SEIS,
                                    _get_person_agent, _get_software_agent)
from gmprocess.stationstream import StationStream
from gmprocess.streamcollection import StreamCollection
from gmprocess.metrics.station_summary import StationSummary, XML_UNITS
from gmprocess.exception import GMProcessException
from gmprocess.event import ScalarEvent

TIMEPAT = '[0-9]{4}-[0-9]{2}-[0-9]{2}T'
EVENT_TABLE_COLUMNS = ['id', 'time', 'latitude',
                       'longitude', 'depth', 'magnitude', 'magnitude_type']
NON_IMT_COLUMNS = ['ELEVATION', 'EPICENTRAL_DISTANCE',
                   'HYPOCENTRAL_DISTANCE', 'LAT', 'LON',
                   'NAME', 'NETID', 'SOURCE', 'STATION']

# List of columns in the flatfile, along with their descriptions for the README
FLATFILE_COLUMNS = {
    'EarthquakeId': 'Event ID from Comcat',
    'EarthquakeTime': 'Earthquake origin time (UTC)',
    'EarthquakeLatitude': 'Earthquake latitude (decimal degrees)',
    'EarthquakeLongitude': 'Earthquake longitude (decimal degrees)',
    'EarthquakeDepth': 'Earthquake depth (km)',
    'EarthquakeMagnitude': 'Earthquake magnitude',
    'EarthquakeMagnitudeType': 'Earthquake magnitude type',
    'Network': 'Network code',
    'DataProvider': 'Data source provider',
    'StationCode': 'Station code',
    'StationID': 'Concatenated network, station, and instrument codes',
    'StationDescription': 'Station description',
    'StationLatitude': 'Station latitude (decimal degrees)',
    'StationLongitude': 'Station longitude (decimal degrees)',
    'StationElevation': 'Station elevation (m)',
    'SamplingRate': 'Record sampling rate (Hz)',
    'BackAzimuth': 'Site-to-source azimuth (decimal degrees)',
    'EpicentralDistance': 'Epicentral distance (km)',
    'HypocentralDistance': 'Hypocentral distance (km)',
    'RuptureDistance': 'Closest distance to the rupture plane (km)',
    'RuptureDistanceVar': 'Variance of rupture distance estimate (km^2)',
    'JoynerBooreDistance': 'Joyner-Boore distance (km)',
    'JoynerBooreDistanceVar':
        'Variance of Joyner-Boore distance estimate (km^2)',
    'GC2_rx': (
        'Distance measured perpendicular to the fault strike from the surface'
        ' projection of the up-dip edge of the fault plane (km)'),
    'GC2_ry': (
        'Distance measured parallel to the fault strike from the midpoint of '
        'the surface projection of the fault plane (km)'),
    'GC2_ry0': (
        'Horizontal distance off the end of the rupture measured parallel to '
        'strike (km)'),
    'GC2_U': (
        'Strike-normal (U) coordinate, defined by Spudich and Chiou (2015; '
        'https://doi.org/10.3133/ofr20151028) (km)'),
    'GC2_T': (
        'Strike-parallel (T) coordinate, defined by Spudich and Chiou '
        '(2015; https://doi.org/10.3133/ofr20151028) (km)'),
    'H1Lowpass': 'H1 channel lowpass frequency (Hz)',
    'H1Highpass': 'H1 channel highpass frequency (Hz)',
    'H2Lowpass': 'H2 channel lowpass frequency (Hz)',
    'H2Highpass': 'H2 channel highpass frequency (Hz)',
    'SourceFile': 'Source file'}

FLATFILE_IMT_COLUMNS = {
    'PGA': 'Peak ground acceleration (%s)'
           % XML_UNITS['pga'],
    'PGV': 'Peak ground velocity (%s)'
           % XML_UNITS['pgv'],
    'SA(X)': 'Pseudo-spectral acceleration (%s) at X seconds'
           % XML_UNITS['sa'],
    'FAS(X)': 'Fourier amplitude spectrum value (%s) at X seconds'
           % XML_UNITS['fas'],
    'DURATION': '5-95 percent significant duration (%s)'
           % XML_UNITS['duration'],
    'ARIAS': 'Arias intensity (%s)'
           % XML_UNITS['arias']
}

# List of columns in the fit_spectra_parameters file, along README descriptions
FIT_SPECTRA_COLUMNS = {
    'EarthquakeId': 'Event ID from Comcat',
    'EarthquakeTime': 'Earthquake origin time (UTC)',
    'EarthquakeLatitude': 'Earthquake latitude (decimal degrees)',
    'EarthquakeLongitude': 'Earthquake longitude (decimal degrees)',
    'EarthquakeDepth': 'Earthquake depth (km)',
    'EarthquakeMagnitude': 'Earthquake magnitude',
    'EarthquakeMagnitudeType': 'Earthquake magnitude type',
    'TraceID': 'NET.STA.LOC.CHA',
    'StationLatitude': 'Station latitude (decimal degrees)',
    'StationLongitude': 'Station longitude (decimal degrees)',
    'StationElevation': 'Station elevation (m)',
    'fmin': 'Record highpass filter frequency (Hz)',
    'fmax': 'Record lowpass filter frequency (Hz)',
    'epi_dist': 'Epicentral distance (km)',
    'f0': 'Brune corner frequency (Hz)',
    'kappa': 'Site diminution factor (sec)',
    'magnitude': 'Magnitude from optimized moment',
    'minimize_message':
        'Output message from scipy.optimize.minimize',
    'minimize_success':
        'Boolean flag indicating if the optimizer exited successfully',
    'moment': 'Moment fit (dyne-cm)',
    'moment_lnsd': 'Natural log standard deviation of the moment fit',
    'stress_drop': 'Stress drop fit (bars)',
    'stress_drop_lnsd':
        'Natural log standard deviation of the stress drop fit',
}


M_PER_KM = 1000

FORMAT_VERSION = '1.0'


def format_netsta(stats):
    return '{st.network}.{st.station}'.format(st=stats)


def format_nslc(stats):
    #loc = '' if stats.location == '--' else stats.location
    return '{st.network}.{st.station}.{st.location}.{st.channel}'.format(
        st=stats)


def format_nslct(stats, tag):
    return format_nslc(stats) + '_' + tag


def format_nslit(stats, inst, tag):
    #loc = '' if stats.location == '--' else stats.location
    return '{st.network}.{st.station}.{st.location}.{inst}_{tag}'.format(
        st=stats, inst=inst, tag=tag)


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

    def close(self):
        """Close the workspace.

        """
        del self.dataset

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

        # Creating a new provenance document and filling in the software
        # information for every trace can be slow, so here we create a
        # base provenance document that will be copied and used as a template
        base_prov = prov.model.ProvDocument()
        base_prov.add_namespace(*NS_SEIS)
        base_prov = _get_person_agent(base_prov)
        base_prov = _get_software_agent(base_prov)

        for stream in streams:
            station = stream[0].stats['station']
            logging.info('Adding waveforms for station %s' % station)
            # is this a raw file? Check the trace for provenance info.
            is_raw = not len(stream[0].getProvenanceKeys())

            if label is None:
                tfmt = '%Y%m%d%H%M%S'
                tnow = UTCDateTime.now().strftime(tfmt)
                label = 'processed%s' % tnow
            tag = '{}_{}'.format(eventid, label)
            if is_raw:
                level = 'raw'
            else:
                level = 'processed'
            self.dataset.add_waveforms(stream, tag=tag, event_id=event)

            # add processing provenance info from traces
            if level == 'processed':
                provdocs = stream.getProvenanceDocuments(base_prov)
                for provdoc, trace in zip(provdocs, stream):
                    provname = format_nslct(trace.stats, tag)
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
                parampath = '/'.join([
                    format_netsta(stream[0].stats),
                    format_nslit(stream[0].stats, stream.get_inst(), tag)
                ])
                self.dataset.add_auxiliary_data(
                    jsonarray,
                    data_type=dtype,
                    path=parampath,
                    parameters={}
                )

            # add processing parameters from traces
            for trace in stream:
                procname = '/'.join([format_netsta(trace.stats),
                                     format_nslct(trace.stats, tag),
                                     ])
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

                # Some processing data is computationally intensive to
                # compute, so we store it in the 'Cache' group.
                for specname in trace.getCachedNames():
                    spectrum = trace.getCached(specname)
                    # we expect many of these specnames to
                    # be joined with underscores.
                    name_parts = specname.split('_')
                    base_dtype = ''.join([part.capitalize()
                                          for part in name_parts])
                    for array_name, array in spectrum.items():
                        path = base_dtype + array_name.capitalize() + "/" + procname
                        try:
                            self.dataset.add_auxiliary_data(
                                array,
                                data_type='Cache',
                                path=path,
                                parameters={}
                            )
                        except Exception as e:
                            pass
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
        all_labels = list(set([at.split('_')[-1] for at in all_tags]))
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

        for waveform in self.dataset.ifilter(
            self.dataset.q.station == stations,
            self.dataset.q.tag == ['%s_%s' % (eventid, label)
                                   for label in labels]):
            tags = waveform.get_waveform_tags()
            for tag in tags:
                tstream = waveform[tag]

                inventory = waveform['StationXML']
                for ttrace in tstream:
                    if isinstance(ttrace.data[0], np.floating):
                        if ttrace.data[0].nbytes == 4:
                            ttrace.data = ttrace.data.astype('float32')
                        else:
                            ttrace.data = ttrace.data.astype('float64')
                    else:
                        if ttrace.data[0].nbytes == 2:
                            ttrace.data = ttrace.data.astype('int16')
                        elif ttrace.data[0].nbytes == 4:
                            ttrace.data = ttrace.data.astype('int32')
                        else:
                            ttrace.data = ttrace.data.astype('int64')
                    trace = StationTrace(data=ttrace.data,
                                         header=ttrace.stats,
                                         inventory=inventory)

                    # get the provenance information
                    provname = format_nslct(trace.stats, tag)
                    if provname in self.dataset.provenance.list():
                        provdoc = self.dataset.provenance[provname]
                        trace.setProvenanceDocument(provdoc)

                    # get the trace processing parameters
                    top = format_netsta(trace.stats)
                    trace_path = format_nslct(trace.stats, tag)
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
                    if 'Cache' in self.dataset.auxiliary_data:
                        for aux in self.dataset.auxiliary_data['Cache'].list():
                            auxarray = self.dataset.auxiliary_data['Cache'][aux]
                            if top not in auxarray.list():
                                continue
                            auxarray_top = auxarray[top]
                            if trace_path in auxarray_top:
                                specparts = camel_case_split(aux)
                                array_name = specparts[-1].lower()
                                specname = '_'.join(specparts[:-1]).lower()
                                specarray = auxarray_top[trace_path].data[()]
                                if specname in spectra:
                                    spectra[specname][array_name] = specarray
                                else:
                                    spectra[specname] = {array_name: specarray}
                        for key, value in spectra.items():
                            trace.setCached(key, value)

                    stream = StationStream(traces=[trace])
                    stream.tag = tag  # testing this out

                    # get the stream processing parameters
                    stream_path = format_nslit(
                        trace.stats, stream.get_inst(), tag)
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

    def calcMetrics(self, eventid, stations=None, labels=None, config=None,
                    streams=None, stream_label=None, rupture_file=None,
                    calc_station_metrics=True, calc_waveform_metrics=True):
        """
        Calculate waveform and/or station metrics for a set of waveforms.
        Args:
            eventid (str):
                ID of event to search for in ASDF file.
            stations (list):
                List of stations to create metrics for.
            labels (list):
                List of processing labels to create metrics for.
            config (dict):
                Configuration dictionary.
            streams (StreamCollection):
                Optional StreamCollection object to create metrics for.
            stream_label (str):
                Label to be used in the metrics path when providing a
                StreamCollection.
            rupture_file (str):
                Path pointing to the rupture file.
            calc_station_metrics (bool):
                Whether to calculate station metrics. Default is True.
            calc_waveform_metrics (bool):
                Whether to calculate waveform metrics. Default is True.
        """
        if not self.hasEvent(eventid):
            fmt = 'No event matching %s found in workspace.'
            raise KeyError(fmt % eventid)

        if streams is None:
            streams = self.getStreams(eventid, stations=stations,
                                      labels=labels)

        event = self.getEvent(eventid)

        # Load the rupture file
        origin = Origin({
            'id': event.id,
            'netid': '',
            'network': '',
            'lat': event.latitude,
            'lon': event.longitude,
            'depth': event.depth_km,
            'locstring': '',
            'mag': event.magnitude,
            'time': event.time})
        rupture = get_rupture(origin, rupture_file)

        vs30_grids = None
        if config is not None:
            if 'vs30' in config['metrics']:
                vs30_grids = config['metrics']['vs30']
                for vs30_name in vs30_grids:
                    vs30_grids[vs30_name]['grid_object'] = GMTGrid.load(
                        vs30_grids[vs30_name]['file'])

        for stream in streams:
            instrument = stream.get_id()
            logging.info('Calculating stream metrics for %s...' % instrument)

            try:
                summary = StationSummary.from_config(
                    stream, event=event, config=config,
                    calc_waveform_metrics=calc_waveform_metrics,
                    calc_station_metrics=calc_station_metrics,
                    rupture=rupture, vs30_grids=vs30_grids)
            except Exception as pgme:
                fmt = ('Could not create stream metrics for event %s,'
                       'instrument %s: "%s"')
                logging.warning(fmt % (eventid, instrument, str(pgme)))
                continue

            if calc_waveform_metrics and stream.passed:
                xmlstr = summary.get_metric_xml()
                if stream_label is not None:
                    tag = '%s_%s' % (eventid, stream_label)
                else:
                    tag = stream.tag
                metricpath = '/'.join([
                    format_netsta(stream[0].stats),
                    format_nslit(stream[0].stats, stream.get_inst(), tag),
                ])
                self.insert_aux(xmlstr, 'WaveFormMetrics', metricpath)

            if calc_station_metrics:
                xmlstr = summary.get_station_xml()
                metricpath = '/'.join([
                    format_netsta(stream[0].stats),
                    format_nslit(stream[0].stats, stream.get_inst(), eventid)
                ])
                self.insert_aux(xmlstr, 'StationMetrics', metricpath)

    def getTables(self, label, streams=None, stream_label=None):
        '''Retrieve dataframes containing event information and IMC/IMT metrics.

        Args:
            label (str):
                Calculate metrics only for the given label.
            streams (StreamCollection):
                Optional StreamCollection object to get tables for.
            stream_label (str):
                Label to be used in the metrics path when providing a
                StreamCollection.

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
                   - dictionary of README DataFrames, where keys are IMCs
                     and values are DataFrames with columns:
                     - Column header
                     - Description
        '''
        event_info = []
        imc_tables = {}
        readme_tables = {}
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
            event_info.append(edict)

            if streams is None:
                streams = self.getStreams(eventid, labels=[label])

            for stream in streams:
                if not stream.passed:
                    continue

                station = stream[0].stats.station
                network = stream[0].stats.network
                summary = self.getStreamMetrics(
                    eventid, network, station, label, streams=[stream],
                    stream_label=stream_label)

                if summary is None:
                    continue

                pgms = summary.pgms
                imclist = pgms.index.get_level_values('IMC').unique().tolist()
                imtlist = pgms.index.get_level_values('IMT').unique().tolist()
                imtlist.sort(key=_natural_keys)

                # Add any Vs30 columns to the list of FLATFILE_COLUMNS
                for vs30_dict in summary._vs30.values():
                    FLATFILE_COLUMNS[vs30_dict['column_header']] = \
                        vs30_dict['readme_entry']

                for imc in imclist:
                    if imc not in imc_tables:
                        row = _get_table_row(stream, summary, event, imc)
                        if not len(row):
                            continue
                        imc_tables[imc] = [row]
                    else:
                        row = _get_table_row(stream, summary, event, imc)
                        if not len(row):
                            continue
                        imc_tables[imc].append(row)

        # Remove any empty IMT columns from the IMC tables
        for key, table in imc_tables.items():
            table = pd.DataFrame.from_dict(table)
            have_imts = []
            for imt in list(set(table.columns) & set(imtlist)):
                if not pd.isna(table[imt]).all():
                    have_imts.append(imt)
            have_imts.sort(key=_natural_keys)
            table = table[list(FLATFILE_COLUMNS.keys()) + have_imts]
            imc_tables[key] = table
            readme_dict = {}
            for col in table.columns:
                if col in FLATFILE_COLUMNS:
                    readme_dict[col] = FLATFILE_COLUMNS[col]
                else:
                    imt = col.upper()
                    if imt.startswith('SA'):
                        readme_dict['SA(X)'] = FLATFILE_IMT_COLUMNS['SA(X)']
                    elif imt.startswith('FAS'):
                        readme_dict['FAS(X)'] = FLATFILE_IMT_COLUMNS['FAS(X)']
                    else:
                        readme_dict[imt] = FLATFILE_IMT_COLUMNS[imt]
            df_readme = pd.DataFrame.from_dict(readme_dict, orient='index')
            df_readme.reset_index(level=0, inplace=True)
            df_readme.columns = ['Column header', 'Description']
            readme_tables[key] = df_readme

        event_table = pd.DataFrame.from_dict(event_info)
        return (event_table, imc_tables, readme_tables)

    def getFitSpectraTable(self, eventid, label, streams):
        """
        Returns a tuple of two pandas DataFrames. The first contains the
        fit_spectra parameters for each trace in the workspace matching
        eventid and label. The second is a README describing each column
        in the first DataFrame.

        Args:
            eventid (str):
                Return parameters only for the given eventid.
            label (str):
                Return parameters only for the given label.
            streams (StreamCollection):
                Optional StreamCollection object to get parameters for.

        Returns:
            pandas.DataFrame:
                A DataFrame containing the fit_spectra parameters on a trace-
                by-trace basis.
        """
        fit_table = []
        event = self.getEvent(eventid)
        if streams is None:
            streams = self.getStreams(eventid, labels=[label])
        for st in streams:
            if not st.passed:
                continue
            for tr in st:
                if tr.hasParameter('fit_spectra'):
                    fit_dict = tr.getParameter('fit_spectra')
                    fit_dict['EarthquakeId'] = eventid
                    fit_dict['EarthquakeTime'] = event.time
                    fit_dict['EarthquakeLatitude'] = event.latitude
                    fit_dict['EarthquakeLongitude'] = event.longitude
                    fit_dict['EarthquakeDepth'] = event.depth_km
                    fit_dict['EarthquakeMagnitude'] = event.magnitude
                    fit_dict['EarthquakeMagnitudeType'] = event.magnitude_type
                    fit_dict['TraceID'] = tr.id
                    fit_dict['StationLatitude'] = tr.stats.coordinates.latitude
                    fit_dict['StationLongitude'] = \
                        tr.stats.coordinates.longitude
                    fit_dict['StationElevation'] = \
                        tr.stats.coordinates.elevation
                    if tr.hasParameter('corner_frequencies'):
                        freq_dict = tr.getParameter('corner_frequencies')
                        fit_dict['fmin'] = freq_dict['highpass']
                        fit_dict['fmax'] = freq_dict['lowpass']
                    fit_table.append(fit_dict)

        if len(fit_table):
            df = pd.DataFrame.from_dict(fit_table)
        else:
            df = pd.DataFrame(columns=FIT_SPECTRA_COLUMNS.keys())

        readme = pd.DataFrame.from_dict(FIT_SPECTRA_COLUMNS, orient='index')
        readme.reset_index(level=0, inplace=True)
        readme.columns = ['Column header', 'Description']

        return (df, readme)

    def getStreamMetrics(self, eventid, network, station, label, streams=None,
                         stream_label=None):
        """Extract a StationSummary object from the ASDF file for a given input Stream.

        Args:
            eventid (str):
                ID of event to search for in ASDF file.
            network (str):
                Network to return metrics from.
            station (str):
                Station to return metrics from.
            label (str):
                Processing label to return metrics from.
            streams (StreamCollection):
                Optional StreamCollection object to get metrics for.
            stream_label (str):
                Label to be used in the metrics path when providing a
                StreamCollection.

        Returns:
            StationSummary: Object containing all stream metrics or None.
        """
        if 'WaveFormMetrics' not in self.dataset.auxiliary_data:
            msg = ('Waveform metrics not found in workspace, '
                   'cannot get stream metrics.')
            logging.warning(msg)
            return None

        auxholder = self.dataset.auxiliary_data.WaveFormMetrics

        # get the stream matching the eventid, station, and label
        if streams is None:
            streams = self.getStreams(eventid, stations=[station],
                                      labels=[label])

        # Only get streams that passed and match network
        streams = [st for st in streams if
                   (st.passed and st[0].stats.network == network)]

        if not len(streams):
            fmt = '''Stream matching event ID %s,
            station ID %s, and processing label %s not found in workspace.'''
            msg = fmt % (eventid, station, label)
            logging.warning(msg)
            return None

        if stream_label is not None:
            stream_tag = '%s_%s' % (eventid, stream_label)
        else:
            stream_tag = streams[0].tag

        metricpath = format_nslit(streams[0][0].stats,
                                  streams[0].get_inst(),
                                  stream_tag)
        top = format_netsta(streams[0][0].stats)
        if top in auxholder:
            tauxholder = auxholder[top]
            if metricpath not in tauxholder:
                fmt = 'Stream metrics path (%s) not in WaveFormMetrics auxiliary_data.'
                logging.warning(fmt % metricpath)
                return None

            bytelist = tauxholder[metricpath].data[:].tolist()
            xml_stream = ''.join([chr(b) for b in bytelist])
            xml_stream = xml_stream.encode('utf-8')
        else:
            return

        if 'StationMetrics' not in self.dataset.auxiliary_data:
            logging.warning('Station metrics not found in workspace.')
            return None
        auxholder = self.dataset.auxiliary_data.StationMetrics
        station_path = format_nslit(
            streams[0][0].stats, streams[0].get_inst(), eventid)
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
        else:
            return

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
        labels = list(set([ptag.split('_')[-1] for ptag in provtags]))
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
        df_dicts = []
        for provname in self.dataset.provenance.list():
            has_station = False
            for station in stations:
                if station in provname:
                    has_station = True
                    break
            has_label = False
            for label in labels:
                if label in provname:
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
                    df_dicts.append(row)

        df = pd.DataFrame.from_dict(df_dicts)
        df = df[cols]

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

    dists = summary.distances

    row = {'EarthquakeId': event.id,
           'EarthquakeTime': event.time,
           'EarthquakeLatitude': event.latitude,
           'EarthquakeLongitude': event.longitude,
           'EarthquakeDepth': event.depth_km,
           'EarthquakeMagnitude': event.magnitude,
           'EarthquakeMagnitudeType': event.magnitude_type,
           'Network': stream[0].stats.network,
           'DataProvider': stream[0].stats.standard.source,
           'StationCode': stream[0].stats.station,
           'StationID': stream.get_id(),
           'StationDescription': stream[0].stats.standard.station_name,
           'StationLatitude': stream[0].stats.coordinates.latitude,
           'StationLongitude': stream[0].stats.coordinates.longitude,
           'StationElevation': stream[0].stats.coordinates.elevation,
           'SamplingRate': stream[0].stats.sampling_rate,
           'BackAzimuth': summary._back_azimuth,
           'EpicentralDistance': dists['epicentral'],
           'HypocentralDistance': dists['hypocentral'],
           'RuptureDistance': dists['rupture'],
           'RuptureDistanceVar': dists['rupture_var'],
           'JoynerBooreDistance': dists['joyner_boore'],
           'JoynerBooreDistanceVar': dists['joyner_boore_var'],
           'GC2_rx': dists['gc2_rx'],
           'GC2_ry': dists['gc2_ry'],
           'GC2_ry0': dists['gc2_ry0'],
           'GC2_U': dists['gc2_U'],
           'GC2_T': dists['gc2_T'],
           'H1Lowpass': h1_lowpass,
           'H1Highpass': h1_highpass,
           'H2Lowpass': h2_lowpass,
           'H2Highpass': h2_highpass,
           'SourceFile': stream[0].stats.standard.source_file}

    # Add the Vs30 values to the row
    for vs30_dict in summary._vs30.values():
        row[vs30_dict['column_header']] = vs30_dict['value']

    imt_frame = summary.pgms.xs(imc, level=1)
    row.update(imt_frame.Result.to_dict())
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
