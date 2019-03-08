# stdlib imports
import json

# third party imports
import numpy as np
from obspy.core.stream import Stream
from obspy.core.utcdatetime import UTCDateTime
from obspy.core.inventory import (Inventory, Network, Station,
                                  Channel, Site, Equipment)
# local imports
from .stationtrace import StationTrace

UNITS = {'acc': 'cm/s/s',
         'vel': 'cm/s'}
REVERSE_UNITS = {'cm/s/s': 'acc',
                 'cm/s': 'vel'}

# if we find places for these in the standard metadata,
# remove them from this list. Anything here will
# be extracted from the stats standard dictionary,
# combined with the format_specific dictionary,
# serialized to json and stored in the station description.
UNUSED_STANDARD_PARAMS = ['instrument_period',
                          'instrument_damping',
                          'process_time',
                          'process_level',
                          'structure_type',
                          'corner_frequency']


class StationStream(Stream):
    def __init__(self, traces=None, inventory=None):
        super(StationStream, self).__init__()

        if len(traces):
            for trace in traces:
                if inventory is None:
                    if not isinstance(trace, StationTrace):
                        raise ValueError(
                            'Input Traces to StationStream must be of subtype '
                            'StationTrace')
                    else:
                        self.append(trace)
                else:
                    if not isinstance(trace, StationTrace):
                        statrace = StationTrace(data=trace.data,
                                                header=trace.stats,
                                                inventory=inventory)
                        self.append(statrace)
                    else:
                        self.append(trace)
        self.passed = True

    def __str__(self, indent=0):
        """
        String summary of the StationStream.
        """
        if self.traces:
            id_length = self and max(len(tr.id) for tr in self) or 0
        else:
            id_length = 0
        if self.passed:
            pass_str = ' (passed)'
        else:
            pass_str = ' (failed)'
        ind_str = ' ' * indent
        out = ('%s StationTrace(s) in StationStream%s:\n%s'
               % (ind_str + str(len(self.traces)), pass_str, ind_str))
        lc = [_i.__str__(id_length, indent) for _i in self]
        out += ("\n" + ind_str).join(lc)
        return out

    def getInventory(self):
        """Extract an ObsPy inventory object from a Stream read in by gmprocess tools.
        """
        networks = [trace.stats.network for trace in self]
        if len(set(networks)) > 1:
            raise Exception(
                "Input stream has stations from multiple networks.")

        # We'll first create all the various objects. These strongly follow the
        # hierarchy of StationXML files.
        source = ''
        if 'standard' in self[0].stats and 'source' in self[0].stats.standard:
            source = self[0].stats.standard.source
        inv = Inventory(
            # We'll add networks later.
            networks=[],
            # The source should be the id whoever create the file.
            source=source)

        net = Network(
            # This is the network code according to the SEED standard.
            code=networks[0],
            # A list of stations. We'll add one later.
            stations=[],
            description="source",
            # Start-and end dates are optional.
        )
        channels = []
        for trace in self:
            channel = _channel_from_stats(trace.stats)
            channels.append(channel)

        subdict = {}
        for k in UNUSED_STANDARD_PARAMS:
            if k in self[0].stats.standard:
                subdict[k] = self[0].stats.standard[k]

        format_specific = {}
        if 'format_specific' in self[0].stats:
            format_specific = dict(self[0].stats.format_specific)

        big_dict = {'standard': subdict,
                    'format_specific': format_specific}
        jsonstr = json.dumps(big_dict)
        sta = Station(
            # This is the station code according to the SEED standard.
            code=self[0].stats.station,
            latitude=self[0].stats.coordinates.latitude,
            elevation=self[0].stats.coordinates.elevation,
            longitude=self[0].stats.coordinates.longitude,
            channels=channels,
            site=Site(name=self[0].stats.standard.station_name),
            description=jsonstr,
            creation_date=UTCDateTime(1970, 1, 1),  # this is bogus
            total_number_of_channels=len(self))

        net.stations.append(sta)
        inv.networks.append(net)

        return inv

    def check_stream(self):
        """
        Processing checks get regorded as a 'failure' parameter in
        StationTraces. Streams also need to be classified as passed/faild,
        where if any of the checks have failed for consistent traces then the
        stream has failed.
        """
        stream_checks = []
        for tr in self:
            stream_checks.append(tr.hasParameter('failure'))
        if any(stream_checks):
            self.passed = False
        else:
            self.passed = True


def _channel_from_stats(stats):
    if stats.standard.units in UNITS:
        units = UNITS[stats.standard.units]
    else:
        units = ''
    instrument = stats.standard.instrument
    serialnum = stats.standard.sensor_serial_number
    if len(instrument) or len(serialnum):
        equipment = Equipment(type=instrument,
                              serial_number=serialnum)
    else:
        equipment = None
    depth = 0.0
    azimuth = None
    c1 = 'horizontal_orientation' in stats.standard
    c2 = c1 and not np.isnan(stats.standard.horizontal_orientation)
    if c2:
        azimuth = stats.standard.horizontal_orientation
    else:
        azimuth = 0

    response = None
    if 'response' in stats:
        response = stats['response']
    channel = Channel(stats.channel,
                      stats.location,
                      stats.coordinates['latitude'],
                      stats.coordinates['longitude'],
                      stats.coordinates['elevation'],
                      depth,
                      azimuth=azimuth,
                      sample_rate=stats.sampling_rate,
                      storage_format=stats.standard.source_format,
                      calibration_units=units,
                      comments=stats.standard.comments,
                      response=response,
                      sensor=equipment)
    return channel
