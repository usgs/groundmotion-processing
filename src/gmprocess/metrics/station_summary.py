# stdlib imports
import logging
import re

# third party imports
from lxml import etree
import numpy as np
import pandas as pd
from obspy.core.stream import Stream
from obspy.geodetics.base import gps2dist_azimuth
from openquake.hazardlib.geo.geodetic import distance
from esi_utils_rupture.point_rupture import PointRupture

# local imports
from gmprocess.utils.config import get_config
from gmprocess.metrics.gather import gather_pgms
from gmprocess.metrics.metrics_controller import MetricsController
from gmprocess.utils.constants import (
    ELEVATION_FOR_DISTANCE_CALCS,
    METRICS_XML_FLOAT_STRING_FORMAT,
)
from gmprocess.utils.tables import _get_table_row, find_float

XML_UNITS = {
    "pga": "%g",
    "pgv": "cm/s",
    "sa": "%g",
    "arias": "m/s",
    "fas": "cm/s",
    "duration": "s",
    "sorted_duration": "s",
}

DEFAULT_DAMPING = 0.05

M_PER_KM = 1000


class StationSummary(object):
    """
    Class for returning pgm values for specific components.
    """

    def __init__(self):
        self._bandwidth = None
        self._components = None
        self._coordinates = None
        self._damping = None
        self._elevation = None
        self._distances = {}
        self._back_azimuth = None
        self._vs30 = {}
        self._imts = None
        self._event = None
        self._pgms = None
        self._smoothing = None
        self._starttime = None
        self._station_code = None
        self._stream = None
        self._summary = None
        self.channel_dict = {}

    @property
    def available_imcs(self):
        """
        Helper method for getting a list of components.

        Returns:
            list: List of available components (str).
        """
        return [x for x in gather_pgms()[1]]

    @property
    def available_imts(self):
        """
        Helper method for getting a list of measurement types.

        Returns:
            list: List of available measurement types (str).
        """
        return [x for x in gather_pgms()[0]]

    @property
    def bandwidth(self):
        """
        Helper method for getting the defined bandwidth.

        Returns:
            float: Bandwidth used in smoothing.
        """
        return self._bandwidth

    @property
    def components(self):
        """
        Helper method returning a list of requested/calculated components.

        Returns:
            list: List of requested/calculated components (str).
        """
        return list(self._components)

    @property
    def coordinates(self):
        """
        Helper method returning the coordinates of the station.

        Returns:
            list: List of coordinates (str).
        """
        return self._coordinates

    @property
    def damping(self):
        """
        Helper method for getting the damping used in the spectral amplitude
        calculation.

        Returns:
            float: Damping used in SA calculation.
        """
        return self._damping

    @property
    def elevation(self):
        """
        Helper method for getting the station elevation.

        Returns:
            float: Station elevation
        """
        return self._elevation

    @property
    def distances(self):
        """
        Helper method for getting the distances.

        Returns:
            dict: Dictionary of distance measurements.
        """
        return self._distances

    @classmethod
    def from_config(
        cls,
        stream,
        config=None,
        event=None,
        calc_waveform_metrics=True,
        calc_station_metrics=True,
        rupture=None,
    ):
        """
        Args:
            stream (obspy.core.stream.Stream):
                Strong motion timeseries for one station.
            config (dictionary):
                Configuration dictionary.
            event (ScalarEvent):
                Object containing latitude, longitude, depth, and magnitude.
            calc_waveform_metrics (bool):
                Whether to calculate waveform metrics. Default is True.
            calc_station_metrics (bool):
                Whether to calculate station metrics. Default is True.
            rupture (PointRupture or QuadRupture):
                esi-utils-rupture rupture object. Default is None.

        Returns:
            class: StationSummary class.

        Note:
            Assumes a processed stream with units of gal (1 cm/s^2).
            No processing is done by this class.
        """
        if config is None:
            config = get_config()
        station = cls()

        damping = config["metrics"]["sa"]["damping"]
        smoothing = config["metrics"]["fas"]["smoothing"]
        bandwidth = config["metrics"]["fas"]["bandwidth"]

        station._damping = damping
        station._smoothing = smoothing
        station._bandwidth = bandwidth
        station._stream = stream
        station.event = event
        station.set_metadata()

        if stream.passed and calc_waveform_metrics:
            metrics = MetricsController.from_config(stream, config=config, event=event)

            station.channel_dict = metrics.channel_dict.copy()

            pgms = metrics.pgms
            if pgms is None:
                station._components = metrics.imcs
                station._imts = metrics.imts
                station.pgms = pd.DataFrame.from_dict(
                    {"IMT": [], "IMC": [], "Result": []}
                )
            else:
                station._components = set(pgms.index.get_level_values("IMC"))
                station._imts = set(pgms.index.get_level_values("IMT"))
                station.pgms = pgms
        if calc_station_metrics:
            station.compute_station_metrics(rupture)

        return station

    @classmethod
    def from_pgms(cls, station_code, pgms):
        """
        Args:
            station_code (str):
                Station code for the given pgms.
            pgms (dict):
                Dictionary of pgms.

        Returns:
            class: StationSummary clsas.

        Note:
            The pgm dictionary must be formated as imts with subdictionaries
            containing imcs:

            ```
                {
                  'SA1.0': {
                    'H2': 84.23215974982956,
                    'H1': 135.9267934939141,
                    'GREATER_OF_TWO_HORIZONTALS': 135.9267934939141,
                    'Z': 27.436966897028416
                  },
                  ...
                }
            ```

            This should be the default format for significant ground motion
            parametric data from COMCAT.
        """
        station = cls()
        station._station_code = station_code
        dfdict = {"IMT": [], "IMC": [], "Result": []}
        for imt in pgms:
            for imc in pgms[imt]:
                dfdict["IMT"] += [imt]
                dfdict["IMC"] += [imc]
                dfdict["Result"] += [pgms[imt][imc]]
        pgmdf = pd.DataFrame.from_dict(dfdict).set_index(["IMT", "IMC"])
        station.pgms = pgmdf
        imts = [key for key in pgms]
        components = []
        for imt in pgms:
            components += [imc for imc in pgms[imt]]
        station._components = np.sort(np.unique(components))
        station._imts = np.sort(imts)
        # stream should be set later with corrected a corrected stream
        # this stream (in units of gal or 1 cm/s^2) can be used to
        # calculate and set oscillators
        return station

    @classmethod
    def from_stream(
        cls,
        stream,
        components,
        imts,
        event=None,
        damping=None,
        smoothing=None,
        bandwidth=None,
        allow_nans=None,
        config=None,
        calc_waveform_metrics=True,
        calc_station_metrics=True,
        rupture=None,
    ):
        """
        Args:
            stream (obspy.core.stream.Stream):
                Strong motion timeseries for one station.
            components (list):
                List of requested components (str).
            imts (list):
                List of requested imts (str).
            event (ScalarEvent):
                Origin/magnitude for the event containing time, latitude,
                longitude, depth, and magnitude.
            damping (float):
                Damping of oscillator. Default is None.
            smoothing (float):
                Smoothing method. Default is None.
            bandwidth (float):
                Bandwidth of smoothing. Default is None.
            allow_nans (bool):
                Should nans be allowed in the smoothed spectra. If False, then
                the number of points in the FFT will be computed to ensure
                that nans will not result in the smoothed spectra.
            config (dictionary):
                Configuration dictionary.
            calc_waveform_metrics (bool):
                Whether to calculate waveform metrics. Default is True.
            calc_station_metrics (bool):
                Whether to calculate station metrics. Default is True.
            rupture (PointRupture or QuadRupture):
                esi-utils-rupture rupture object. Default is None.
        Note:
            Assumes a processed stream with units of gal (1 cm/s^2).
            No processing is done by this class.
        """
        if config is None:
            config = get_config()
        station = cls()
        imts = np.sort(imts)
        components = np.sort(components)

        if damping is None:
            damping = config["metrics"]["sa"]["damping"]
        if smoothing is None:
            smoothing = config["metrics"]["fas"]["smoothing"]
        if bandwidth is None:
            bandwidth = config["metrics"]["fas"]["bandwidth"]
        if allow_nans is None:
            allow_nans = config["metrics"]["fas"]["allow_nans"]

        station._damping = damping
        station._smoothing = smoothing
        station._bandwidth = bandwidth
        station._stream = stream
        station.event = event
        station.set_metadata()

        if stream.passed and calc_waveform_metrics:
            metrics = MetricsController(
                imts,
                components,
                stream,
                bandwidth=bandwidth,
                allow_nans=allow_nans,
                damping=damping,
                event=event,
                smooth_type=smoothing,
            )
            station.channel_dict = metrics.channel_dict.copy()
            pgms = metrics.pgms

            if pgms.empty:
                station._components = metrics.imcs
                station._imts = metrics.imts
                station.pgms = pd.DataFrame.from_dict(
                    {"IMT": [], "IMC": [], "Result": []}
                )
            else:
                station._components = set(pgms.index.get_level_values("IMC"))
                station._imts = set(pgms.index.get_level_values("IMT"))
                station.pgms = pgms
        if calc_station_metrics:
            station.compute_station_metrics(rupture)
        return station

    def get_pgm(self, imt, imc):
        """
        Finds the imt/imc value requested.

        Args:
            imt (str):
                Requested intensity measure type.
            imc (str):
                Requested intensity measure component.

        Returns:
            float: Value for the imt, imc requested.
        """
        imt = imt.upper()
        imc = imc.upper()
        if imt not in self.imts or imc not in self.components:
            return np.nan
        else:
            return self.pgms.Result.loc[imt, imc]

    def get_summary(self):
        columns = ["STATION", "NAME", "SOURCE", "NETID", "LAT", "LON", "ELEVATION"]
        if self._distances is not None:
            for dist_type in self._distances:
                columns.append(dist_type.upper() + "_DISTANCE")
        if self._vs30 is not None:
            for vs30_type in self._vs30:
                columns.append(vs30_type.upper())
        # set meta_data
        row = np.zeros(len(columns), dtype=list)
        row[0] = self.station_code
        name_str = self.stream[0].stats["standard"]["station_name"]
        row[1] = name_str
        source = self.stream[0].stats.standard["source"]
        row[2] = source
        row[3] = self.stream[0].stats["network"]
        row[4] = self.coordinates[0]
        row[5] = self.coordinates[1]
        row[6] = self.elevation
        imcs = self.components
        imts = self.imts
        pgms = self.pgms
        meta_columns = pd.MultiIndex.from_product([columns, [""]])
        meta_dataframe = pd.DataFrame(np.array([row]), columns=meta_columns)
        pgm_columns = pd.MultiIndex.from_product([imcs, imts])
        pgm_data = np.zeros((1, len(imts) * len(imcs)))
        subindex = 0
        for imc in imcs:
            for imt in imts:
                try:
                    value = pgms.Result.loc[imt, imc]
                except KeyError:
                    value = np.nan
                pgm_data[0][subindex] = value
                subindex += 1
        pgm_dataframe = pd.DataFrame(pgm_data, columns=pgm_columns)
        dataframe = pd.concat([meta_dataframe, pgm_dataframe], axis=1)
        return dataframe

    @property
    def imts(self):
        """
        Helper method returning a list of requested/calculated measurement
        types.

        Returns:
            list: List of requested/calculated measurement types (str).
        """
        return list(self._imts)

    @property
    def pgms(self):
        """
        Helper method returning a station's pgms.

        Returns:
            dictionary: Pgms for each imt and imc.
        """
        return self._pgms

    @pgms.setter
    def pgms(self, pgms):
        """
        Helper method to set the pgms attribute.

        Args:
            pgms (list): Dictionary of pgms for each imt and imc.
        """
        self._pgms = pgms

    def set_metadata(self):
        """
        Set the metadata for the station
        """
        stats = self.stream[0].stats
        self._starttime = stats.starttime
        self._station_code = stats.station
        if "coordinates" not in stats:
            self._elevation = np.nan
            self._coordinates = (np.nan, np.nan)
            return
        lat = stats.coordinates.latitude
        lon = stats.coordinates.longitude
        if "elevation" not in stats.coordinates or np.isnan(
            stats.coordinates.elevation
        ):
            elev = 0
        else:
            elev = stats.coordinates.elevation
        self._elevation = elev
        self._coordinates = (lat, lon)

    @property
    def smoothing(self):
        """
        Helper method for getting the defined smoothing used for the
        calculation FAS.

        Returns:
            string: Smoothing method used.
        """
        return self._smoothing

    @property
    def starttime(self):
        """
        Helper method returning a station's starttime.

        Returns:
            str: Start time for one station.
        """
        return self._starttime

    @property
    def station_code(self):
        """
        Helper method returning a station's station code.

        Returns:
            str: Station code for one station.
        """
        return self._station_code

    @property
    def stream(self):
        """
        Helper method returning a station's stream.

        Returns:
            obspy.core.stream.Stream: Stream for one station.
        """
        return self._stream

    @stream.setter
    def stream(self, stream):
        """
        Helper method to set the stream attribute.

        Args:
            stream (obspy.core.stream.Stream): Stream for one station.
        """
        if self.stream is not None:
            logging.warning(
                "Setting failed: the stream object cannot be "
                "changed. A new instance of StationSummary must be created."
            )
        else:
            if not isinstance(stream, Stream):
                logging.warning("Setting failed: not a stream object.")
            elif stream[0].stats["station"].upper() != self.station_code.upper():
                logging.warning(
                    "Setting failed: stream station does not match "
                    "StationSummary.station_code."
                )
            else:
                self._stream = stream

    @property
    def summary(self):
        """
        Helper method returning a station's summary.

        Returns:
            pandas.Dataframe: Summary for one station.
        """
        return self.get_summary()

    @classmethod
    def from_xml(cls, xml_stream, xml_station):
        """Instantiate a StationSummary from metrics XML stored in ASDF file.

        <waveform_metrics>
            <rot_d50>
                <pga units="m/s**2">0.45</pga>
                <sa percent_damping="5.0" units="g">
                <value period="2.0">0.2</value>
            </rot_d50>
            <maximum_component>
            </maximum_component>
        </waveform_metrics>

        <station_metrics>
            <distances>
            <hypocentral units="km">100</hypocentral>
            <epicentral units="km">120</epicentral>
            </distances>
        </station_metrics>

        Args:
            xml_stream (str):
                Stream metrics XML string in format above.
            xml_station (str):
                Station metrics XML string in format above.

        Returns:
            object: StationSummary Object summarizing all station metrics.

        """
        imtlist = gather_pgms()[0]
        root = etree.fromstring(xml_stream)
        pgms = {}
        channel_dict = {}
        damping = None
        for element in root.iter():
            etag = element.tag
            if etag == "waveform_metrics":
                station_code = element.attrib["station_code"]
                continue
            elif etag in imtlist:
                tdict = {}
                if etag in ["sa", "fas"]:
                    period = element.attrib["period"]
                    if "damping" in element.attrib:
                        damping = float(element.attrib["damping"])
                    imt = f"{etag.upper()}({period})"
                elif etag == "duration":
                    interval = element.attrib["interval"]
                    imt = f"{etag.upper()}{interval}"
                else:
                    imt = etag.upper()
                for imc_element in element.getchildren():
                    imc = imc_element.tag.upper()
                    if imc in ["H1", "H2", "Z"]:
                        if "original_channel" in imc_element.attrib:
                            channel_dict[imc] = imc_element.attrib["original_channel"]
                    value = float(imc_element.text)
                    tdict[imc] = value

                pgms[imt] = tdict
        station = cls.from_pgms(station_code, pgms)
        station._damping = damping
        station.channel_dict = channel_dict.copy()
        # extract info from station metrics, fill in metadata
        root = etree.fromstring(xml_station)  # station metrics element
        for element in root.iterchildren():
            if element.tag == "distances":
                for dist_type in element.iterchildren():
                    station._distances[dist_type.tag] = float(dist_type.text)
            if element.tag == "vs30":
                for vs30_type in element.iterchildren():
                    station._vs30[vs30_type.tag] = {
                        "value": float(vs30_type.text),
                        "column_header": vs30_type.attrib["column_header"],
                        "readme_entry": vs30_type.attrib["readme_entry"],
                        "units": vs30_type.attrib["units"],
                    }
            if element.tag == "back_azimuth":
                station._back_azimuth = float(element.text)

        return station

    def compute_station_metrics(self, rupture=None):
        """
        Computes station metrics (distances, vs30, back azimuth) for the
        StationSummary.

        Args:
            rupture (PointRupture or QuadRupture):
                esi-utils-rupture rupture object. Default is None.
        """
        lat, lon = self.coordinates
        elev = self.elevation
        if self.event is not None:
            event = self.event
            dist, baz, _ = gps2dist_azimuth(lat, lon, event.latitude, event.longitude)
            self._distances["epicentral"] = dist / M_PER_KM
            self._back_azimuth = baz
            if event.depth is not None:
                self._distances["hypocentral"] = distance(
                    lon,
                    lat,
                    -elev / M_PER_KM,
                    event.longitude,
                    event.latitude,
                    event.depth / M_PER_KM,
                )

        if rupture is not None:
            lon = np.array([lon])
            lat = np.array([lat])
            elev = np.array([ELEVATION_FOR_DISTANCE_CALCS])

            rrup, rrup_var = rupture.computeRrup(lon, lat, elev)
            rjb, rjb_var = rupture.computeRjb(lon, lat, elev)
            gc2_dict = rupture.computeGC2(lon, lat, elev)

            if not isinstance(rupture, PointRupture):
                rrup_var = np.full_like(rrup, np.nan)
                rjb_var = np.full_like(rjb, np.nan)

                # If we don't have a point rupture, then back azimuth needs
                # to be calculated to the closest point on the rupture
                dists = []
                bazs = []
                for quad in rupture._quadrilaterals:
                    P0, P1, P2, P3 = quad
                    for point in [P0, P1]:
                        dist, az, baz = gps2dist_azimuth(point.y, point.x, lat, lon)
                        dists.append(dist)
                        bazs.append(baz)
                self._back_azimuth = bazs[np.argmin(dists)]
            else:
                gc2_dict = {x: [np.nan] for x in gc2_dict}

            self._distances.update(
                {
                    "rupture": rrup[0],
                    "rupture_var": rrup_var[0],
                    "joyner_boore": rjb[0],
                    "joyner_boore_var": rjb_var[0],
                    "gc2_rx": gc2_dict["rx"][0],
                    "gc2_ry": gc2_dict["ry"][0],
                    "gc2_ry0": gc2_dict["ry0"][0],
                    "gc2_U": gc2_dict["U"][0],
                    "gc2_T": gc2_dict["T"][0],
                }
            )

    def get_metric_xml(self):
        """Return waveform metrics XML as defined for our ASDF implementation.

        Returns:
            str: XML in the form:
                <waveform_metrics>
                    <rot_d50>
                        <pga units="m/s**2">0.45</pga>
                        <sa percent_damping="5.0" units="g">
                        <value period="2.0">0.2</value>
                    </rot_d50>
                    <maximum_component>
                    </maximum_component>
                </waveform_metrics>

        Raises:
            KeyError: if the requrested imt is not present.
        """
        FLOAT_MATCH = r"[0-9]*\.[0-9]*"
        root = etree.Element("waveform_metrics", station_code=self.station_code)
        for imt in self.imts:
            imtstr = imt.lower()
            units = None
            if imtstr in XML_UNITS:
                units = XML_UNITS[imtstr]
            else:
                for key in XML_UNITS.keys():
                    if imtstr.startswith(key):
                        units = XML_UNITS[key]
                        break
            if units is None:
                raise KeyError(f"Could not find units for IMT {imtstr}")

            period = None
            if imtstr.startswith("sa") or imtstr.startswith("fas"):
                period = float(re.search(FLOAT_MATCH, imtstr).group())
                attdict = {
                    "period": (METRICS_XML_FLOAT_STRING_FORMAT["period"] % period),
                    "units": units,
                }
                if imtstr.startswith("sa"):
                    imtstr = "sa"
                    damping = self._damping
                    if damping is None:
                        damping = DEFAULT_DAMPING
                    attdict["damping"] = (
                        METRICS_XML_FLOAT_STRING_FORMAT["damping"] % damping
                    )
                else:
                    imtstr = "fas"
                imt_tag = etree.SubElement(root, imtstr, attrib=attdict)
            elif imtstr.startswith("duration"):
                attdict = {"interval": imtstr.replace("duration", ""), "units": units}
                imtstr = "duration"
                imt_tag = etree.SubElement(root, imtstr, attrib=attdict)
            else:
                imt_tag = etree.SubElement(root, imtstr, units=units)

            for imc in self.components:
                imcstr = imc.lower().replace("(", "").replace(")", "")
                if imc in ["H1", "H2", "Z"]:
                    attributes = {"original_channel": self.channel_dict[imc]}
                else:
                    attributes = {}
                imc_tag = etree.SubElement(imt_tag, imcstr, attrib=attributes)
                try:
                    value = self.pgms.Result.loc[imt, imc]
                except KeyError:
                    value = np.nan
                imc_tag.text = METRICS_XML_FLOAT_STRING_FORMAT["pgm"] % value
        xmlstr = etree.tostring(root, pretty_print=True, encoding="unicode")
        return xmlstr

    def get_station_xml(self):
        """
        Return XML for station metrics as defined for our ASDF
        implementation.

        Returns:
            str: XML in the form specified by format.
        """

        root = etree.Element("station_metrics", station_code=self.station_code)

        if self._back_azimuth is not None:
            back_azimuth = etree.SubElement(root, "back_azimuth")
            back_azimuth.text = (
                METRICS_XML_FLOAT_STRING_FORMAT["back_azimuth"] % self._back_azimuth
            )

        if self._distances:
            distances = etree.SubElement(root, "distances")
            for dist_type in self._distances:
                element = etree.SubElement(distances, dist_type, units="km")
                element.text = (
                    METRICS_XML_FLOAT_STRING_FORMAT["distance"]
                    % self._distances[dist_type]
                )

        if self._vs30:
            vs30 = etree.SubElement(root, "vs30")
            for vs30_type in self._vs30:
                element = etree.SubElement(
                    vs30,
                    vs30_type,
                    units=self._vs30[vs30_type]["units"],
                    column_header=self._vs30[vs30_type]["column_header"],
                    readme_entry=self._vs30[vs30_type]["readme_entry"],
                )
                element.text = (
                    METRICS_XML_FLOAT_STRING_FORMAT["vs30"]
                    % self._vs30[vs30_type]["value"]
                )

        return etree.tostring(root, pretty_print=True, encoding="unicode")

    def toSeries(self):
        """Render StationSummary as a Pandas Series object.

        Returns:
            Series:
                Multi-Indexed Pandas Series where IMTs are top-level indices
                and components are sub-indices.
        """
        imts = self.imts
        imcs = self.components
        index = pd.MultiIndex.from_product([imts, imcs])
        data = []
        for imt in imts:
            for imc in imcs:
                idx = (self.pgms.IMT == imt) & (self.pgms.IMC == imc)
                vals = self.pgms[idx].Result.tolist()
                if len(vals) == 0:
                    value = np.nan
                else:
                    value = vals[0]
                data.append(value)
        series = pd.Series(data, index)
        return series

    def get_imc_dict(self, imc=None):
        """Get an IMC table.

        Args:
            imc (str or list):
                String of list of strings specifying the requested IMC.

        Returns:
            A dictionary with keys corresponding to IMCs, where the associated
            value is a dictionary with keys corresponding to IMTs.
        """
        imc_dict = {}
        pgms = self.pgms
        if imc is None:
            imclist = pgms.index.get_level_values("IMC").unique().tolist()
        elif not isinstance(imc, list):
            imclist = [imc]
        else:
            imclist = imc

        # Note: in this situation, we can only have 1 row per "table" where the
        # different IMTs are the different columns.
        for imc in imclist:
            row = _get_table_row(self._stream, self, self.event, imc)
            if not len(row):
                continue
            imc_dict[imc] = row
        return imc_dict

    def get_sa_arrays(self, imc=None):
        """Get an SA arrays for selected IMCs.

        Args:
            imc (str or list):
                String of list of strings specifying the requested IMC.

        Returns:
            A dictionary with keys corresponding to IMCs, where the associated
            value is a dictionary with keys of 'period' and 'sa' which are
            numpy arrays.
        """
        imc_dict = self.get_imc_dict(imc)
        sa_arrays = {}
        for imc_key, id in imc_dict.items():
            period = []
            sa = []
            for imt, val in id.items():
                tmp_period = find_float(imt)
                if tmp_period is not None:
                    period.append(tmp_period)
                    sa.append(val)
            period = np.array(period)
            sa = np.array(sa)
            idx = np.argsort(period)
            sa_arrays[imc_key] = {"period": period[idx], "sa": sa[idx]}
        return sa_arrays
