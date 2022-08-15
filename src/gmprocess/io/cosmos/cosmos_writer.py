# stdlib imports
import logging
import pathlib
import re
import time
from collections import OrderedDict
from datetime import datetime
from enum import Enum

# third party imports
import numpy as np
import pandas as pd
import scipy.constants as sp
from gmprocess.core.stationtrace import TIMEFMT, UNITS

# local imports
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.cosmos.core import BUILDING_TYPES, MICRO_TO_VOLT, SENSOR_TYPES
from gmprocess.utils.config import get_config
from obspy.geodetics.base import gps2dist_azimuth

COSMOS_FORMAT = 1.2
UTC_TIME_FMT = "%m/%d/%Y, %H:%M:%S.%f"
AGENCY_RESERVED = "Converted from ASDF"
LOCAL_TIME_FMT = "%B %d, %Y %H:%M"


class Volume(Enum):
    RAW = 0
    CONVERTED = 1
    PROCESSED = 2


HEADER_LINES = 13
NUM_INT_VALUES = 100
INT_FMT = "%8d"
NUM_INT_ROWS = 10
NUM_INT_COLS = 10

NUM_FLOAT_VALUES = 100
FLOAT_FMT = "%13.6f"
NUM_FLOAT_ROWS = 17
NUM_FLOAT_COLS = 6

NUM_DATA_COLS = 8
DATA_FMT = "%10.5f"

TABLE1 = {"acc": 1, "vel": 2}
TABLE2 = {"acc": 4, "vel": 5}
TABLE7 = {
    "US": 2,
    "BK": 3,
    "CI": 4,
    "NC": 5,
    "AZ": 7,
    "NN": 8,
    "C_": 9,
    " -": 10,
    "CE": 11,
    "TW": 100,
    "JP": 110,
    "BO": 111,
    "": 200,
}
SEISMIC_TRIGGER = 1
MISSING_DATA_INT = -999
MISSING_DATA_FLOAT = -999

REV_BUILDING_TYPES = {v: k for k, v in BUILDING_TYPES.items()}
REV_SENSOR_TYPES = {v: k for k, v in SENSOR_TYPES.items()}
CAUSAL_BUTTERWORTH_FILTER = 4
NONCAUSAL_BUTTERWORTH_FILTER = 5
FREQ_DOMAIN_FILTER = 1


def cfmt_to_ffmt(cfmt, ncols):
    ffmt = cfmt.replace("%", "")
    if "d" in cfmt:
        ffmt = str(ncols) + "I" + ffmt.replace("d", "")
    else:
        ffmt = str(ncols) + "F" + ffmt.replace("f", "")
    return ffmt


TEXT_HEADER_LINES = [
    ("param_type", "cosmos_format", "number_lines", "agency_reserved"),
    ("event_name", "event_local_time"),
    (
        "event_latitude",
        "event_longitude",
        "event_depth",
        "event_source",
        "event_magnitude",
    ),
    ("event_time", "source_agency"),
    (
        "network_number",
        "station_number",
        "network_code",
        "station_code",
        "network_abbrev",
        "station_name",
    ),
    ("station_latitude", "station_longitude", "site_geology"),
    (
        "recorder_type",
        "recorder_serial",
        "recorder_channels",
        "station_channels",
        "sensor_type",
        "sensor_serial",
    ),
    ("record_start", "time_quality", "record_id"),
    (
        "channel_number",
        "channel_azimuth",
        "recorder_channel_number",
        "sensor_location",
    ),
    ("record_duration", "raw_maximum", "raw_maximum_units", "raw_maximum_time"),
    (
        "processing_date",
        "data_maximum",
        "data_maximum_units",
        "data_maximum_time",
    ),
    ("low_band_hz", "low_band_sec", "high_band_hz"),
    ("missing_data_str", "missing_data_int", "missing_data_float"),
]


class Table4(object):
    def __init__(self, excelfile):
        self._dataframe = pd.read_excel(excelfile, na_filter=False)

    def get_cosmos_code(self, iris_code):
        row = self.get_row(iris_code)
        cosmos_code = row["Cosmos Code"]
        return cosmos_code

    def get_agency_desc(self, iris_code):
        row = self.get_row(iris_code)
        agency = row["Agency"]
        return agency

    def get_agency_abbrev(self, iris_code):
        row = self.get_row(iris_code)
        abbrev = row["Abbrev"]
        return abbrev

    def get_matching_network(self, eventid):
        eventid = eventid.lower()
        for _, row in self._dataframe.iterrows():
            network = row["IRIS Code"].lower()
            if eventid.startswith(network):
                return network
        return "--"

    def get_row(self, iris_code):
        iris_code = iris_code.upper()
        rows = self._dataframe.loc[self._dataframe["IRIS Code"] == iris_code]
        if not len(rows):
            iris_code = "--"
        rows = self._dataframe.loc[self._dataframe["IRIS Code"] == iris_code]
        return rows.iloc[0]


class TextHeader(object):
    # header_fmt tuples are (format_string, column offset, and value
    # (filled in by constructor))
    header_fmt = OrderedDict()
    # header_fmt["param_type"] = ["{value:25s}", 0, None]

    # line 1
    header_fmt["param_type"] = ["{value:25s}", 0, None]
    header_fmt["cosmos_format"] = ["(Format v{value:05.2f} ", 26, None]
    header_fmt["number_lines"] = ["with {value:2d} text lines)", 40, None]
    header_fmt["agency_reserved"] = ["{value:19s}", 61, None]

    # line 2
    header_fmt["event_name"] = ["{value:40s}", 0, None]
    header_fmt["event_local_time"] = ["{value:40s}", 40, None]

    # line 3
    header_fmt["event_latitude"] = ["Hypocenter:{value:7.3f}", 0, None]
    header_fmt["event_longitude"] = ["{value:8.3f}", 21, None]
    header_fmt["event_depth"] = ["H={value:3d}km", 32, None]
    header_fmt["event_source"] = ["({value:4s})", 39, None]
    header_fmt["event_magnitude"] = ["M={value:3.1f}", 46, None]

    # line 4
    header_fmt["event_time"] = ["Origin: {value:26s}", 0, None]
    header_fmt["source_agency"] = ["({value:4s})", 35, None]

    # line 5
    header_fmt["network_number"] = ["Statn No: {value:02d}-", 0, None]
    header_fmt["station_number"] = ["{value:5d}", 13, None]
    header_fmt["network_code"] = ["Code:{value:2s}-", 20, None]
    header_fmt["station_code"] = ["{value:6s}", 28, None]
    header_fmt["network_abbrev"] = ["{value:4s}", 35, None]
    header_fmt["station_name"] = ["{value:40s}", 40, None]

    # line 6
    header_fmt["station_latitude"] = ["Coords:{value:-8.4f}", 0, None]
    header_fmt["station_longitude"] = ["{value:-9.4f}", 16, None]
    header_fmt["site_geology"] = ["Site geology:{value:40s}", 27, None]

    # line 7
    header_fmt["recorder_type"] = ["Recorder: {value:6s}", 0, None]
    header_fmt["recorder_serial"] = ["s/n:{value:5s}", 17, None]
    header_fmt["recorder_channels"] = ["({value:3d}", 26, None]
    header_fmt["station_channels"] = [" Chns of {value:2d} at Sta)", 26, None]
    header_fmt["sensor_type"] = ["Sensor:{value:8s}", 50, None]
    header_fmt["sensor_serial"] = ["s/n {value:11s}", 68, None]

    # line 8
    header_fmt["record_start"] = ["Rcrd start time:{value:28s}", 0, None]
    header_fmt["time_quality"] = ["(Q={value:1s})", 45, None]
    header_fmt["record_id"] = ["RcrdId:{value:20s}", 51, None]

    # line 9
    header_fmt["channel_number"] = ["Sta Chan{value:4d}:", 8, None]
    header_fmt["channel_azimuth"] = ["{value:-3d} deg ", 13, None]
    header_fmt["recorder_channel_number"] = ["(Rcrdr Chan{value:3d}) ", 21, None]
    header_fmt["sensor_location"] = ["Location:{value:33s}", 37, None]

    # line 10
    header_fmt["record_duration"] = ["Raw record length ={value:8.3f} sec, ", 0, None]
    header_fmt["raw_maximum"] = ["Uncor max ={value:9.3f} ", 33, None]
    header_fmt["raw_maximum_units"] = ["{value:<6s} ", 53, None]
    header_fmt["raw_maximum_time"] = ["at {value:8.3f} sec", 59, None]

    # line 11
    header_fmt["processing_date"] = ["Processed:{value:28s}", 0, None]
    header_fmt["processing_agency"] = ["{value:5s}", 35, None]
    header_fmt["data_maximum"] = ["Max = {value:9.3f}", 41, None]
    header_fmt["data_maximum_units"] = ["{value:9s}", 57, None]
    header_fmt["data_maximum_time"] = ["at {value:7.3f} sec", 66, None]

    # line 12
    header_fmt["low_band_hz"] = ["Record filtered below{value:6.2f} Hz", 0, None]
    header_fmt["low_band_sec"] = ["(periods over{value:6.1f} secs)", 31, None]
    header_fmt["high_band_hz"] = ["and above{value:5.1f} Hz", 58, None]

    # line 13
    header_fmt["missing_data_str"] = ["{value:64s}", 0, None]
    header_fmt["missing_data_int"] = ["{value:7d}", 64, None]
    header_fmt["missing_data_float"] = ["{value:5.1f}", 72, None]

    def __init__(self, trace, scalar_event, stream, volume, gmprocess_version):
        datadir = pathlib.Path(__file__).parent / ".." / ".." / "data"
        excelfile = pathlib.Path(datadir) / "cosmos_table4.xls"
        table4 = Table4(excelfile)
        # fill in data for text header
        # UNITS = {"acc": "cm/s^2", "vel": "cm/s"}
        quantity = "velocity"
        if trace.stats.standard.units_type == "acc":
            quantity = "acceleration"
        level = "Raw"
        dmax = trace.max()
        maxidx = np.where(trace.data == dmax)[0][0]

        if volume == Volume.CONVERTED:
            level = "Corrected"
            converted = trace.remove_response()
            dmax = converted.max()  # max of absolute value
            maxidx = np.where(converted.data == dmax)[0][0]
        elif volume == Volume.PROCESSED:
            level = "Corrected"
        maxtime = trace.stats.delta * maxidx  # seconds since rec start

        # line 1
        self.set_header_value("param_type", f"{level} {quantity}")
        self.set_header_value("cosmos_format", COSMOS_FORMAT)
        self.set_header_value("number_lines", HEADER_LINES)
        self.set_header_value("agency_reserved", AGENCY_RESERVED)

        # line 2
        ename_str = f"M{scalar_event.magnitude} at {scalar_event.time}"
        self.set_header_value("event_name", ename_str)
        # Leaving local time blank, because it is hard to determine correctly
        self.set_header_value("event_local_time", "")

        # line 3
        self.set_header_value("event_latitude", scalar_event.latitude)
        self.set_header_value("event_longitude", scalar_event.longitude)
        self.set_header_value("event_depth", int(np.round(scalar_event.depth_km)))
        iris_network = table4.get_matching_network(
            scalar_event.id.replace("smi:local/", "")
        )
        abbrev = table4.get_agency_abbrev(iris_network)
        self.set_header_value("event_source", abbrev)
        self.set_header_value("event_magnitude", scalar_event.magnitude)

        # line 4
        etime = scalar_event.time.strftime(UTC_TIME_FMT)[:-5] + " UTC"
        self.set_header_value("event_time", etime)
        self.set_header_value("source_agency", abbrev)

        # line 5
        netnum = table4.get_cosmos_code(trace.stats.network)
        self.set_header_value("network_number", netnum)
        self.set_header_value("station_number", 0)
        self.set_header_value("network_code", trace.stats.network)
        self.set_header_value("station_code", trace.stats.station)
        self.set_header_value(
            "network_abbrev", table4.get_agency_abbrev(trace.stats.network)
        )
        self.set_header_value("station_name", trace.stats.standard.station_name)

        # line 6
        self.set_header_value("station_latitude", trace.stats.coordinates.latitude)
        self.set_header_value("station_longitude", trace.stats.coordinates.longitude)
        self.set_header_value("site_geology", "Unknown")

        # line 7
        self.set_header_value("recorder_type", "")
        self.set_header_value("recorder_serial", "")
        self.set_header_value("recorder_channels", len(stream))
        self.set_header_value("station_channels", len(stream))
        instrument = trace.stats.standard.instrument.replace("None", "").strip()
        self.set_header_value("sensor_type", instrument)
        self.set_header_value(
            "sensor_serial", trace.stats.standard.sensor_serial_number
        )

        # line 8
        stime = trace.stats.starttime.strftime(UTC_TIME_FMT)[:-3] + " UTC"
        self.set_header_value("record_start", stime)
        # we don't know time quality, set to blank value
        self.set_header_value("time_quality", "")
        record_id = (
            f"{trace.stats.network}.{trace.stats.station}."
            f"{trace.stats.channel}.{trace.stats.location}"
        )
        self.set_header_value("record_id", record_id)

        # line 9
        channels = [trace.stats.channel for trace in stream]
        channel_number = channels.index(trace.stats.channel) + 1
        self.set_header_value("channel_number", channel_number)
        azimuth = trace.stats.standard.horizontal_orientation
        if trace.stats.standard.horizontal_orientation == 0:
            azimuth = 360.0
        self.set_header_value("channel_azimuth", int(azimuth))
        self.set_header_value("recorder_channel_number", channel_number)
        self.set_header_value("sensor_location", trace.stats.location)

        # line 10
        dtime = trace.stats.endtime - trace.stats.starttime  # duration secs
        self.set_header_value("record_duration", dtime)
        if volume == Volume.RAW:
            self.set_header_value("raw_maximum", trace.max())
            self.set_header_value(
                "raw_maximum_units", UNITS[trace.stats.standard.units_type]
            )
            self.set_header_value("raw_maximum_time", maxtime)
        else:
            self.set_header_value("raw_maximum", 0)
            self.set_header_value("raw_maximum_units", "")
            self.set_header_value("raw_maximum_time", 0)

        # line 11
        ptimestr = trace.stats.standard.process_time
        pdate = ""
        if len(ptimestr.strip()):
            ptime = datetime.strptime(ptimestr, TIMEFMT)
            pdate = ptime.strftime(UTC_TIME_FMT) + " UTC"
        self.set_header_value("processing_date", pdate)
        config = get_config()
        agency = "UNK"
        if "agency" in config:
            agency = config["agency"]
        self.set_header_value("processing_agency", agency)
        self.set_header_value("data_maximum", dmax)
        self.set_header_value(
            "data_maximum_units", UNITS[trace.stats.standard.units_type]
        )
        self.set_header_value("data_maximum_time", maxtime)

        # line 12
        lowpass_info = trace.getProvenance("lowpass_filter")
        highpass_info = trace.getProvenance("highpass_filter")
        self.set_header_value("low_band_hz", highpass_info[0]["corner_frequency"])
        self.set_header_value("low_band_sec", 1 / highpass_info[0]["corner_frequency"])
        self.set_header_value("high_band_hz", lowpass_info[0]["corner_frequency"])

        # line 13
        miss_str = "Values used when parameter or data value is unknown/unspecified:"
        self.set_header_value("missing_data_str", miss_str)
        self.set_header_value("missing_data_int", MISSING_DATA_INT)
        self.set_header_value("missing_data_float", MISSING_DATA_FLOAT)

    def set_header_value(self, key, value):
        width = int(re.search(r"\d+", self.header_fmt[key][0]).group(0))
        if isinstance(value, str) and len(value) > width:
            value = value[0:width]
        formatted_value = self.header_fmt[key][0].format(value=value)
        self.header_fmt[key][2] = formatted_value

    def write(self, cosmos_file):
        # write out data for text header to cosmos_file object
        for line_keys in TEXT_HEADER_LINES:
            line = ""
            for line_key in line_keys:
                _, column_offset, value = self.header_fmt[line_key]
                offset = column_offset - len(line)
                line += " " * offset + value

            line += (80 - len(line)) * " "
            cosmos_file.write(line + "\n")
        return None


class IntHeader(object):
    def __init__(self, trace, scalar_event, stream, volume, gmprocess_version):
        self.volume = volume
        self.scalar_event = scalar_event
        datadir = pathlib.Path(__file__).parent / ".." / ".." / "data"
        excelfile = pathlib.Path(datadir) / "cosmos_table4.xls"
        table4 = Table4(excelfile)
        ffmt = cfmt_to_ffmt(INT_FMT, NUM_INT_COLS)
        self.start_line = (
            f"{NUM_INT_VALUES:4d}  Integer-header values follow on "
            f"{NUM_INT_ROWS} lines, Format= ({ffmt})"
        )
        self.start_line += (80 - len(self.start_line)) * " "

        # fill in data for int header
        self.header = np.ones((NUM_INT_ROWS, NUM_INT_COLS)) * MISSING_DATA_INT

        # Data/File Parameters
        # Note that notation here is that the indices indicate row/column number as
        # described in the COSMOS documentation.
        self.header[0][0] = volume.value
        self.header[0][1] = TABLE1[trace.stats.standard.units_type]
        self.header[0][2] = TABLE2[trace.stats.standard.units_type]
        self.header[0][3] = int(COSMOS_FORMAT * 100)
        self.header[0][4] = SEISMIC_TRIGGER

        # Station Parameters
        self.header[1][0] = table4.get_cosmos_code(trace.stats.network)
        stype = trace.stats.standard.structure_type
        if not len(stype):
            stype = "Unspecified"
        self.header[1][8] = REV_BUILDING_TYPES[stype]
        self.header[2][2] = len(stream)

        # Earthquake Parameters
        iris_network = table4.get_matching_network(
            scalar_event.id.replace("smi:local/", "")
        ).upper()
        if iris_network in TABLE7:
            source_code = TABLE7[iris_network]
        else:
            source_code = 200

        self.header[2][4] = source_code
        self.header[2][5] = source_code
        self.header[2][6] = source_code
        self.header[2][7] = source_code

        # Record Parameters
        self.header[3][9] = trace.stats.starttime.year
        self.header[4][0] = trace.stats.starttime.julday
        self.header[4][1] = trace.stats.starttime.month
        self.header[4][2] = trace.stats.starttime.day
        self.header[4][3] = trace.stats.starttime.hour
        self.header[4][4] = trace.stats.starttime.minute

        # Sensor/channel Parameters
        channels = [trace.stats.channel for trace in stream]
        channel_number = channels.index(trace.stats.channel) + 1
        self.header[4][9] = channel_number
        azimuth = trace.stats.standard.horizontal_orientation

        # 0 degrees is not an accepted azimuth angle...
        if azimuth == 0.0:
            azimuth = 360.0
        self.header[5][3] = azimuth

        # Filtering/processing parameters
        if volume == Volume.PROCESSED:
            lowpass_info = trace.getProvenance("lowpass_filter")[0]
            highpass_info = trace.getProvenance("highpass_filter")[0]
            self.header[5][9] = NONCAUSAL_BUTTERWORTH_FILTER
            if highpass_info["number_of_passes"] == 1:
                self.header[5][9] = CAUSAL_BUTTERWORTH_FILTER
            self.header[6][1] = NONCAUSAL_BUTTERWORTH_FILTER
            if lowpass_info["number_of_passes"] == 1:
                self.header[6][1] = CAUSAL_BUTTERWORTH_FILTER
            self.header[6][3] = FREQ_DOMAIN_FILTER
        # Response spectrum parameters
        # Miscellaneous

    def write(self, cosmos_file):
        # write out data for int header to cosmos_file object
        cosmos_file.write(self.start_line + "\n")
        fmt = [INT_FMT] * NUM_INT_COLS
        np.savetxt(cosmos_file, self.header, fmt=fmt, delimiter="")


class FloatHeader(object):
    def __init__(self, trace, scalar_event, volume):
        self.volume = volume
        # fill in data for float header
        # fill in data for int header
        ffmt = cfmt_to_ffmt(FLOAT_FMT, NUM_FLOAT_COLS)
        self.start_line = (
            f"{NUM_FLOAT_VALUES} Real-header values follow on "
            f"{NUM_FLOAT_ROWS} lines , Format = ({ffmt})"
        )
        self.header = np.ones((NUM_FLOAT_ROWS, NUM_FLOAT_COLS)) * MISSING_DATA_FLOAT

        # Station parameters
        self.header[0][0] = trace.stats.coordinates.latitude
        self.header[0][1] = trace.stats.coordinates.longitude
        self.header[0][2] = trace.stats.coordinates.elevation

        # Earthquake parameters
        self.header[1][3] = scalar_event.latitude
        self.header[1][4] = scalar_event.longitude
        self.header[1][5] = scalar_event.depth_km
        self.header[1][5] = scalar_event.magnitude
        dist, az, _ = gps2dist_azimuth(
            scalar_event.latitude,
            scalar_event.longitude,
            trace.stats.coordinates.latitude,
            trace.stats.coordinates.longitude,
        )
        self.header[2][4] = dist / 1000  # m to km
        self.header[2][5] = az

        # Recorder/datalogger parameters
        if hasattr(trace.stats.standard, "volts_to_counts"):
            # volts to counts is counts/volt
            # MICRO_TO_VOLT is microvolts/volt
            self.header[3][3] = (
                1 / trace.stats.standard.volts_to_counts
            ) * MICRO_TO_VOLT  # microvolts/count

        # Record parameters
        dtime = (
            len(trace.data) * trace.stats.delta
        )  # duration secs, defined to be npts*dt
        self.header[4][5] = trace.stats.starttime.second
        self.header[5][3] = trace.stats.delta
        self.header[5][4] = dtime

        # Sensor/channel parameters
        self.header[6][3] = 1 / trace.stats.standard.instrument_period
        self.header[6][4] = trace.stats.standard.instrument_damping
        has_sensitivity = hasattr(trace.stats.standard, "instrument_sensitivity")
        has_volts = hasattr(trace.stats.standard, "volts_to_counts")
        if has_sensitivity and has_volts:
            instrument_sensitivity = (
                trace.stats.standard.instrument_sensitivity
            )  # counts/m/s^2
            volts_to_counts = trace.stats.standard.volts_to_counts  # counts/volts
            sensor_sensitivity = (1 / volts_to_counts) * instrument_sensitivity * sp.g
            self.header[6][5] = sensor_sensitivity  # volts/g
        if volume == Volume.PROCESSED:
            lowpass_info = trace.getProvenance("lowpass_filter")[0]
            highpass_info = trace.getProvenance("highpass_filter")[0]
            self.header[8][5] = highpass_info["corner_frequency"]
            self.header[9][2] = lowpass_info["corner_frequency"]

        # time history parameters
        self.header[10][1] = trace.stats.delta * 1000  # msecs
        self.header[10][2] = dtime
        self.header[10][3] = trace.max()
        maxidx = np.where(trace.data == trace.max())[0][0]
        maxtime = trace.stats.delta * maxidx  # seconds since rec start
        self.header[10][4] = maxtime

        self.header[10][5] = trace.data.mean()

        # replace nan values with missing code
        self.header[np.isnan(self.header)] = MISSING_DATA_FLOAT

    def write(self, cosmos_file):
        # write out data for float header to cosmos_file object
        # write out data for int header to cosmos_file object
        cosmos_file.write(self.start_line + "\n")
        fmt = [FLOAT_FMT] * NUM_FLOAT_COLS
        np.savetxt(cosmos_file, self.header, fmt=fmt, delimiter="")


class DataBlock(object):
    def __init__(self, trace, volume, eventid, gmprocess_version):
        datadir = pathlib.Path(__file__).parent / ".." / ".." / "data"
        excelfile = pathlib.Path(datadir) / "cosmos_table4.xls"
        table4 = Table4(excelfile)
        self.volume = volume
        self.trace = trace
        quantity = "velocity"
        if trace.stats.standard.units_type == "acc":
            quantity = "acceleration"
        npts = len(trace.data)
        itime = int(trace.stats.endtime - trace.stats.starttime)  # duration secs
        units = UNITS[trace.stats.standard.units_type]
        ffmt = cfmt_to_ffmt(DATA_FMT, NUM_DATA_COLS)

        # fill in comment fields that we use for overflow information
        self.comment_lines = []
        instrument = trace.stats.standard.instrument.replace("None", "").strip()
        self.write_comment("Sensor", instrument, "standard")
        network = trace.stats.network
        station = trace.stats.station
        channel = trace.stats.channel
        location = trace.stats.location
        event_network = table4.get_matching_network(eventid)
        eventcode = eventid.lower().replace(event_network, "")
        record_id = (
            f"{event_network.upper()}.{eventcode}.{network}."
            f"{station}.{channel}.{location}"
        )
        self.write_comment("RcrdId", record_id, "standard")
        scnl = f"{station}.{channel}.{network}.{location}"
        self.write_comment("SCNL", scnl, "standard")
        pstr = f"Automatically processed using gmprocess version {gmprocess_version}"
        self.write_comment("PROCESS", pstr, "non-standard")

        # fill in data for float header
        self.start_lines = []
        ncomments = len(self.comment_lines)
        self.header_line1 = (
            f'{ncomments} Comment line(s) follow, each starting with a "|":'
        )
        self.header_line2 = (
            f"{npts} {quantity} pts, approx {itime} secs, units={units},Format=({ffmt})"
        )

    def write_comment(self, key, value, comment_type):
        if comment_type == "standard":
            comment = f"| {key}: {value}"
        else:
            comment = f"|<{key}>{value}"
        comment += (80 - len(comment)) * " "  # pad to 80 characters
        self.comment_lines.append(comment)
        return

    def write(self, cosmos_file):
        # write out data for float header to cosmos_file object
        cosmos_file.write(self.header_line1 + "\n")
        for line in self.comment_lines:
            cosmos_file.write(line + "\n")
        cosmos_file.write(self.header_line2 + "\n")
        fmt = [DATA_FMT] * NUM_DATA_COLS
        data = self.trace.data
        if self.volume == Volume.CONVERTED:
            data = self.trace.remove_response()
        data, remainder = split_data(data, NUM_DATA_COLS)
        np.savetxt(cosmos_file, data, fmt=fmt, delimiter="")
        fmt = [DATA_FMT] * len(remainder.T)
        np.savetxt(cosmos_file, remainder, fmt=fmt, delimiter="")


def split_data(data, ncols):
    nrows = int(len(data) / ncols)
    npts = nrows * ncols
    tdata = data[0:npts]
    remainder = data[npts:]
    remainder = np.reshape(remainder, (1, len(remainder)))
    tdata = np.reshape(tdata, (nrows, ncols))
    return (tdata, remainder)


class CosmosWriter(object):
    def __init__(
        self, cosmos_directory, h5_filename, volume=Volume.PROCESSED, label=None
    ):
        if volume == Volume.PROCESSED and label is None:
            raise Exception("Must supply label for processed data")
        self._workspace = StreamWorkspace.open(h5_filename)
        self._cosmos_directory = pathlib.Path(cosmos_directory)
        self._volume = volume
        self._label = label

    def write(self):
        nevents = 0
        nstreams = 0
        ntraces = 0
        files = []
        t_text = []
        t_int = []
        t_float = []
        t_data = []
        t_write = []
        for eventid in self._workspace.getEventIds():
            nevents += 1
            scalar_event = self._workspace.getEvent(eventid)
            gmprocess_version = self._workspace.getGmprocessVersion()
            # remove "dirty" stuff from gmprocess version
            idx = gmprocess_version.find(".dev")
            gmprocess_version = gmprocess_version[0:idx]
            ds = self._workspace.dataset
            station_list = ds.waveforms.list()
            for station_id in station_list:
                streams = self._workspace.getStreams(
                    eventid, stations=[station_id], labels=[self._label]
                )
                for stream in streams:
                    if not stream.passed:
                        continue
                    logging.info(f"Writing stream {stream.id}...")
                    nstreams += 1
                    for trace in stream:
                        net = trace.stats.network
                        sta = trace.stats.station
                        cha = trace.stats.channel
                        loc = trace.stats.location
                        if trace.stats.standard.units_type != "acc":
                            msg = (
                                "Only supporting acceleration data at this "
                                f"time. Skipping channel {cha}."
                            )
                            logging.info(msg)
                            continue
                        ntraces += 1
                        stime = trace.stats.starttime.strftime("%Y%m%d%H%M%S")

                        extension = "V0"
                        if self._volume == Volume.CONVERTED:
                            extension = "V1"
                        elif self._volume == Volume.PROCESSED:
                            extension = "V2"
                        fname = f"{eventid}_{net}_{sta}_{cha}_{loc}_{stime}.{extension}"
                        cosmos_filename = self._cosmos_directory / fname
                        files.append(cosmos_filename)
                        with open(cosmos_filename, "wt") as cosmos_file:
                            logging.debug(f"Getting text header for {trace.id}")
                            t1 = time.time()
                            text_header = TextHeader(
                                trace,
                                scalar_event,
                                stream,
                                self._volume,
                                gmprocess_version,
                            )
                            t2 = time.time()
                            t_text.append(t2 - t1)
                            t1 = time.time()
                            logging.debug(f"Getting int header for {trace.id}")
                            int_header = IntHeader(
                                trace,
                                scalar_event,
                                stream,
                                self._volume,
                                gmprocess_version,
                            )
                            t2 = time.time()
                            t_int.append(t2 - t1)
                            logging.debug(f"Getting float header for {trace.id}")
                            t1 = time.time()
                            float_header = FloatHeader(
                                trace, scalar_event, self._volume
                            )
                            t2 = time.time()
                            t_float.append(t2 - t1)
                            text_header.write(cosmos_file)
                            int_header.write(cosmos_file)
                            float_header.write(cosmos_file)
                            logging.debug(f"Getting data block for {trace.id}")
                            t1 = time.time()
                            data_block = DataBlock(
                                trace, self._volume, eventid, gmprocess_version
                            )
                            t2 = time.time()
                            t_data.append(t2 - t1)
                            t1 = time.time()
                            data_block.write(cosmos_file)
                            t2 = time.time()
                            t_write.append(t2 - t1)
        if ntraces:
            text_av = sum(t_text) / ntraces
            int_av = sum(t_int) / ntraces
            float_av = sum(t_float) / ntraces
            data_av = sum(t_data) / ntraces
            write_av = sum(t_write) / ntraces
            logging.debug(f"Text header mean: {text_av}")
            logging.debug(f"Int header mean: {int_av}")
            logging.debug(f"Float header mean: {float_av}")
            logging.debug(f"Data block mean: {data_av}")
            logging.debug(f"Data write mean: {write_av}")
        else:
            logging.info("No traces processed.")
        return (files, nevents, nstreams, ntraces)

    def __del__(self):
        self._workspace.close()
