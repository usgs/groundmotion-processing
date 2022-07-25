#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import json
import copy
import logging
from datetime import datetime
import getpass
import re
import inspect

# third party imports
import numpy as np
from obspy.core.trace import Trace
import prov
import prov.model
from obspy.core.utcdatetime import UTCDateTime
import pandas as pd
from scipy.integrate import cumtrapz

# local imports
from gmprocess.utils.config import get_config
from gmprocess.io.seedname import get_units_type

UNITS = {"acc": "cm/s^2", "vel": "cm/s"}
REVERSE_UNITS = {
    "cm/s^2": "acc",
    "cm/s**2": "acc",
    "cm/s/s": "acc",
    "cm/s": "vel",
    "cm": "disp",
}

PROCESS_LEVELS = {
    "V0": "raw counts",
    "V1": "uncorrected physical units",
    "V2": "corrected physical units",
    "V3": "derived time series",
}

REV_PROCESS_LEVELS = {
    "raw counts": "V0",
    "uncorrected physical units": "V1",
    "corrected physical units": "V2",
    "derived time series": "V3",
}

LENGTH_CONVERSIONS = {"nm": 1e9, "um": 1e6, "mm": 1e3, "cm": 1e2, "m": 1}

# when checking to see if a channel is vertical,
# 90 - abs(dip) must be less than or equal to this value
# (i.e., dip must ne close to )
MAX_DIP_OFFSET = 0.1

# NOTE: if required is True then this means that the value must be
# filled in with a value that does NOT match the default.
STANDARD_KEYS = {
    "source_file": {"type": str, "required": False, "default": ""},
    "source": {"type": str, "required": True, "default": ""},
    "horizontal_orientation": {"type": float, "required": False, "default": np.nan},
    "vertical_orientation": {"type": float, "required": False, "default": np.nan},
    "station_name": {"type": str, "required": False, "default": ""},
    "instrument_period": {"type": float, "required": False, "default": np.nan},
    "instrument_damping": {"type": float, "required": False, "default": np.nan},
    "process_time": {"type": str, "required": False, "default": ""},
    "process_level": {
        "type": str,
        "required": True,
        "default": list(PROCESS_LEVELS.values()),
    },
    "sensor_serial_number": {"type": str, "required": False, "default": ""},
    "instrument": {"type": str, "required": False, "default": ""},
    "structure_type": {"type": str, "required": False, "default": ""},
    "corner_frequency": {"type": float, "required": False, "default": np.nan},
    "units": {"type": str, "required": True, "default": ""},
    "units_type": {"type": str, "required": True, "default": ""},
    "source_format": {"type": str, "required": True, "default": ""},
    "instrument_sensitivity": {
        "type": float,
        "required": False,
        "default": np.nan,
    },
    "volts_to_counts": {
        "type": float,
        "required": False,
        "default": np.nan,
    },
    "comments": {"type": str, "required": False, "default": ""},
}

INT_TYPES = [
    np.dtype("int8"),
    np.dtype("int16"),
    np.dtype("int32"),
    np.dtype("int64"),
    np.dtype("uint8"),
    np.dtype("uint16"),
    np.dtype("uint32"),
    np.dtype("uint64"),
]

FLOAT_TYPES = [np.dtype("float32"), np.dtype("float64")]

TIMEFMT = "%Y-%m-%dT%H:%M:%SZ"
TIMEFMT_MS = "%Y-%m-%dT%H:%M:%S.%fZ"

NS_PREFIX = "seis_prov"
NS_SEIS = (NS_PREFIX, "http://seisprov.org/seis_prov/0.1/#")

MAX_ID_LEN = 12

PROV_TIME_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"

ACTIVITIES = {
    "waveform_simulation": {"code": "ws", "label": "Waveform Simulation"},
    "taper": {"code": "tp", "label": "Taper"},
    "stack_cross_correlations": {"code": "sc", "label": "Stack Cross Correlations"},
    "simulate_response": {"code": "sr", "label": "Simulate Response"},
    "rotate": {"code": "rt", "label": "Rotate"},
    "resample": {"code": "rs", "label": "Resample"},
    "remove_response": {"code": "rr", "label": "Remove Response"},
    "pad": {"code": "pd", "label": "Pad"},
    "normalize": {"code": "nm", "label": "Normalize"},
    "multiply": {"code": "nm", "label": "Multiply"},
    "merge": {"code": "mg", "label": "Merge"},
    "lowpass_filter": {"code": "lp", "label": "Lowpass Filter"},
    "interpolate": {"code": "ip", "label": "Interpolate"},
    "integrate": {"code": "ig", "label": "Integrate"},
    "highpass_filter": {"code": "hp", "label": "Highpass Filter"},
    "divide": {"code": "dv", "label": "Divide"},
    "differentiate": {"code": "df", "label": "Differentiate"},
    "detrend": {"code": "dt", "label": "Detrend"},
    "decimate": {"code": "dc", "label": "Decimate"},
    "cut": {"code": "ct", "label": "Cut"},
    "cross_correlate": {"code": "co", "label": "Cross Correlate"},
    "calculate_adjoint_source": {"code": "ca", "label": "Calculate Adjoint Source"},
    "bandstop_filter": {"code": "bs", "label": "Bandstop Filter"},
    "bandpass_filter": {"code": "bp", "label": "Bandpass Filter"},
}


class StationTrace(Trace):
    """Subclass of Obspy Trace object which holds more metadata.

    ObsPy provides a Trace object that serves as a container for waveform data
    from a single channel, as well as some basic metadata about the waveform
    start/end times, number of points, sampling rate/interval, and
    network/station/channel/location information.

    gmprocess subclasses the Trace object with a StationTrace object, which
    provides the following additional features:

        - Validation that length of data matches the number of points in the
          metadata.
        - Validation that required values are set in metadata.
        - A `fail` method which can be used by processing routines to mark when
          processing of the StationTrace has failed some sort of check (signal
          to noise ratio, etc.)
        - A `free_field` property which can be used to query the object to
          ensure that its data comes from a free-field sensor. Note: this is
          not always known reliably, and different people have have different
          definitions of the term free_field. When possible, we define a
          mapping between location code and the free_field property. For
          example, see the LOCATION_CODES variable core.py in
          `gmprocess.io.fdsn`.
        - Methods (e.g., `getProvenance`, `setProvenance`) for tracking
          processing steps that have been performed. These are aligned with the
          SEIS-PROV standard for processing provenance, described here:
          http://seismicdata.github.io/SEIS-PROV/_generated_details.html#activities
        - Methods (e.g., `getParameter` and `setParameter`) for tracking of
          arbitrary metadata in the form of a dictionary as trace property
          (self.parameters).
    """

    def __init__(self, data=np.array([]), header=None, inventory=None, config=None):
        """Construct a StationTrace instance.

        Args:
            data (ndarray):
                numpy array of points.
            header (dict-like):
                Dictionary of metadata (see trace.stats docs).
            inventory (Inventory):
                Obspy Inventory object.
            config (dict):
                Dictionary containing configuration.
                If None, retrieve global config.
        """
        prov_response = None
        if config is None:
            config = get_config()
        if inventory is None and header is None:
            raise ValueError(
                "Cannot create StationTrace without header info or Inventory"
            )
        elif inventory is not None and header is not None:
            # End up here if the format was read in with ObsPy and an
            # inventory was able to be constructed (e.g., miniseed+StationXML)
            try:
                seed_id = "%s.%s.%s.%s" % (
                    header["network"],
                    header["station"],
                    header["location"],
                    header["channel"],
                )
                start_time = header["starttime"]
                (response, standard, coords, format_specific) = _stats_from_inventory(
                    data, inventory, seed_id, start_time
                )
                header["response"] = response
                header["coordinates"] = coords
                header["standard"] = standard
                header["format_specific"] = format_specific
            except BaseException as e:
                raise ValueError(
                    "Failed to construct required metadata from inventory "
                    "and input header data with exception: %s" % e
                )
        elif inventory is None and header is not None and "standard" not in header:
            # End up here for ObsPy without an inventory (e.g., SAC).
            # This assumes that all of our readers include the "standard" key
            # in the header and that ObsPy one's do not.

            # NOTE: we are assuming that an ObsPy file that does NOT have an
            # inventory has been converted to cm/s^2 via the configurable
            # conversion factor in the config file.
            prov_response = {"input_units": "counts", "output_units": "cm/s^2"}
            try:
                (response, standard, coords, format_specific) = _stats_from_header(
                    header, config
                )
                header["response"] = response
                header["coordinates"] = coords
                header["standard"] = standard
                header["format_specific"] = format_specific
            except BaseException:
                raise ValueError(
                    "Failed to construct required metadata from header data."
                )

        # Sometimes the channel names do not indicate which one is the
        # Z channel. If we have vertical_orientation information, then
        # let's get that and change the vertical channel to end in Z.
        #     NOTE: `vertical_orientation` here is defined as the angle
        #           from horizontal (aka, dip), not inclination.
        if not np.isnan(header["standard"]["vertical_orientation"]):
            delta = np.abs(np.abs(header["standard"]["vertical_orientation"]) - 90.0)
            is_z = header["channel"].endswith("Z")
            if delta < MAX_DIP_OFFSET and not is_z:
                header["channel"] = header["channel"][0:-1] + "Z"

        # Apply conversion factor if one was specified for this format
        if (
            "format_specific" in header
            and "conversion_factor" in header["format_specific"]
        ):
            data *= header["format_specific"]["conversion_factor"]

        super(StationTrace, self).__init__(data=data, header=header)
        self.provenance = []
        if prov_response is not None:
            self.setProvenance("remove_response", prov_response)
        self.parameters = {}
        self.cached = {}
        self.validate()

    @property
    def free_field(self):
        """Is this station a free-field station?

        Returns:
            bool: True if a free-field sensor, False if not.
        """
        stype = self.stats.standard["structure_type"]
        non_free = [
            "building",
            "bridge",
            "dam",
            "borehole",
            "hole",
            "crest",
            "toe",
            "foundation",
            "body",
            "roof",
            "floor",
        ]
        for ftype in non_free:
            if re.search(ftype, stype.lower()) is not None:
                return False

        return True

    def fail(self, reason):
        """Note that a check on this StationTrace failed for a given reason.

        This method will set the parameter "failure", and store the reason
        provided, plus the name of the calling function.

        Args:
            reason (str):
                Reason given for failure.

        """
        if self.hasParameter("review"):
            review_dict = self.getParameter("review")
            if review_dict["accepted"]:
                return
        istack = inspect.stack()
        calling_module = istack[1][3]
        self.setParameter("failure", {"module": calling_module, "reason": reason})
        trace_id = f"{self.id}"
        logging.info(f"{calling_module} - {trace_id} - {reason}")

    def validate(self):
        """Ensure that all required metadata fields have been set.

        Raises:
            KeyError:
                - When standard dictionary is missing required fields
                - When standard values are of the wrong type
                - When required values are set to a default.
            ValueError:
                - When number of points in header does not match data length.
        """
        # here's something we thought obspy would do...
        # verify that npts matches length of data
        if self.stats.npts != len(self.data):
            raise ValueError(
                "Number of points in header does not match the number of "
                "points in the data."
            )

        if "remove_response" not in self.getProvenanceKeys():
            self.stats.standard.units = "raw counts"
            self.stats.standard.units_type = get_units_type(self.stats.channel)

        # are all of the defined standard keys in the standard dictionary?
        req_keys = set(STANDARD_KEYS.keys())
        std_keys = set(list(self.stats.standard.keys()))
        if not req_keys <= std_keys:
            missing = str(req_keys - std_keys)
            raise KeyError(
                f'Missing standard values in StationTrace header: "{missing}"'
            )
        type_errors = []
        required_errors = []
        for key in req_keys:
            keydict = STANDARD_KEYS[key]
            value = self.stats.standard[key]
            required = keydict["required"]
            vtype = keydict["type"]
            default = keydict["default"]
            if not isinstance(value, vtype):
                type_errors.append(key)
            if required:
                if isinstance(default, list):
                    if value not in default:
                        required_errors.append(key)
                if value == default:
                    required_errors.append(key)

        type_error_msg = ""
        if len(type_errors):
            fmt = 'The following standard keys have the wrong type: "%s"'
            tpl = ",".join(type_errors)
            type_error_msg = fmt % tpl

        required_error_msg = ""
        if len(required_errors):
            fmt = 'The following standard keys are required: "%s"'
            tpl = ",".join(required_errors)
            required_error_msg = fmt % tpl

        error_msg = type_error_msg + "\n" + required_error_msg
        if len(error_msg.strip()):
            raise KeyError(error_msg)

    def differentiate(self, frequency=True):
        input_units = self.stats.standard.units
        if "/s^2" in input_units:
            output_units = input_units.replace("/s^2", "/s^3")
        elif "/s/s" in input_units:
            output_units = input_units.replace("/s/s", "/s/s/s")
        elif "/s" in input_units:
            output_units = input_units.replace("/s", "/s/s")
        else:
            output_units = input_units + "/s"
        if frequency:
            method = "frequency"
            spec_y = np.fft.rfft(self.data, len(self.data))
            freq_y = np.fft.rfftfreq(len(self.data), d=self.stats.delta)
            spec_dy = spec_y * (2j * np.pi * freq_y)
            self.data = np.fft.irfft(spec_dy)
        else:
            method = "gradient"
            self = super().differentiate(method=method)
        self.setProvenance(
            "differentiate",
            {
                "differentiation_method": method,
                "input_units": self.stats.standard.units,
                "output_units": output_units,
            },
        )
        return self

    def integrate(
        self, frequency=False, initial=0.0, demean=False, taper=False, config=None
    ):
        """Integrate a StationTrace with respect to either frequency or time.

        Args:
            frequency (bool):
                Determine if we're integrating in frequency domain.
                If not, integrate in time domain.
            initial (float):
                Define initial value returned in result.
            demean (bool):
                Remove mean from array before integrating.
            taper (bool):
                Taper the ends of entire trace.
            config (dict):
                Configuration dictionary (or None). See get_config().

        Returns:
            StationTrace: Input StationTrace is integrated and returned.
        """
        if config:
            frequency = config["integration"]["frequency"]
            initial = config["integration"]["initial"]
            demean = config["integration"]["demean"]
            taper = config["integration"]["taper"]["taper"]
            taper_width = config["integration"]["taper"]["width"]
            taper_type = config["integration"]["taper"]["type"]
            taper_side = config["integration"]["taper"]["side"]

        if demean:
            self.data -= np.mean(self.data)
            self.setProvenance(
                "demean",
                {
                    "input_units": self.stats.standard.units,
                    "output_units": self.stats.standard.units,
                },
            )

        if taper:
            self.taper(max_percentage=taper_width, type=taper_type, side=taper_side)
            self.setProvenance(
                "taper",
                {
                    "max_percentage": taper_width,
                    "type": taper_type,
                    "side": taper_side,
                    "input_units": self.stats.standard.units,
                    "output_units": self.stats.standard.units,
                },
            )

        if frequency:
            # integrating in frequency domain
            method = "frequency domain"
            # take discrete FFT and get the discretized frequencies
            npts = len(self.data)
            spec_in = np.fft.rfft(self.data, n=npts)
            freq = np.fft.rfftfreq(npts, self.stats.delta)

            # Replace frequency of zero with 1.0 to avoid division by zero. This will
            # cause the DC (mean) to be unchanged by the integration/division.
            freq[0] = 1.0
            spec_out = spec_in / 2.0j / np.pi / freq

            # calculate inverse FFT back to time domain
            integral_result = np.fft.irfft(spec_out, n=npts)

            # Apply initial condition
            shift = integral_result[0] - initial

            self.data = integral_result - shift

        else:
            # integrating in time domain
            method = "time domain"
            integral_result = cumtrapz(self.data, dx=self.stats.delta, initial=initial)
            self.data = integral_result

        input_units = self.stats.standard.units
        if "/s^2" in input_units:
            output_units = input_units.replace("/s^2", "/s")
        elif "/s/s" in input_units:
            output_units = input_units.replace("/s/s", "/s")
        elif "/s" in input_units:
            output_units = input_units.replace("/s", "")
        else:
            output_units = input_units + "*s"
        self.setProvenance(
            "integrate",
            {
                "integration_method": method,
                "input_units": self.stats.standard.units,
                "output_units": output_units,
            },
        )

        return self

    def filter(
        self,
        type="highpass",
        freq=0.05,
        corners=5.0,
        zerophase=False,
        config=None,
        frequency_domain=True,
        **options,
    ):
        """Overwrite parent function to allow for conf options.

        Args:
            type (str):
                What type of filter? "highpass" or "lowpass".
            freq (float):
                Corner frequency (Hz).
            corners (float):
                Number of poles.
            zerophase (bool):
                Zero phase filter?
            config (dict):
                Configuration options.
            frequency_domain (bool):
                Apply filter in frequency domain?
        """
        if zerophase:
            number_of_passes = 2
        else:
            number_of_passes = 1
        if type == "lowpass":

            if not frequency_domain:
                self.setProvenance(
                    "lowpass_filter",
                    {
                        "filter_type": "Butterworth ObsPy",
                        "filter_order": corners,
                        "number_of_passes": number_of_passes,
                        "corner_frequency": freq,
                    },
                )
                return super().filter(
                    type=type,
                    freq=freq,
                    corners=corners,
                    zerophase=zerophase,
                    **options,
                )

            else:
                if zerophase:
                    logging.warning(
                        "Filter is only applied once in frequency domain, "
                        "even if number of passes is 2"
                    )

                # compute fft
                dt = self.stats.delta
                orig_npts = self.stats.npts
                signal_spec = np.fft.rfft(self.data, n=orig_npts)
                signal_freq = np.fft.rfftfreq(orig_npts, dt)
                signal_freq[0] = 1.0

                # apply filter
                filter = np.sqrt(1.0 + (signal_freq / freq) ** (2.0 * corners))
                filtered_spec = signal_spec / filter
                filtered_spec[0] = 0.0
                signal_freq[0] = 0

                # inverse fft to time domain
                filtered_trace = np.fft.irfft(filtered_spec, n=orig_npts)
                # get rid of padded zeros
                self.data = filtered_trace

                self.setProvenance(
                    "lowpass_filter",
                    {
                        "filter_type": "Butterworth gmprocess",
                        "filter_order": corners,
                        "number_of_passes": number_of_passes,
                        "corner_frequency": freq,
                    },
                )

        if type == "highpass":
            if not frequency_domain:
                self.setProvenance(
                    "highpass_filter",
                    {
                        "filter_type": "Butterworth ObsPy",
                        "filter_order": corners,
                        "number_of_passes": number_of_passes,
                        "corner_frequency": freq,
                    },
                )
                return super().filter(
                    type,
                    freq=freq,
                    corners=corners,
                    zerophase=zerophase,
                    **options,
                )

            else:
                if zerophase:
                    logging.warning(
                        "Filter is only applied once in frequency domain, "
                        "even if number of passes is 2"
                    )

                # compute fft
                dt = self.stats.delta
                orig_npts = self.stats.npts
                signal_spec = np.fft.rfft(self.data, n=orig_npts)
                signal_freq = np.fft.rfftfreq(orig_npts, dt)
                signal_freq[0] = 1.0

                # apply filter
                filter = np.sqrt(1.0 + (freq / signal_freq) ** (2.0 * corners))
                filtered_spec = signal_spec / filter
                filtered_spec[0] = 0.0
                signal_freq[0] = 0

                # inverse fft to time domain
                filtered_trace = np.fft.irfft(filtered_spec, n=orig_npts)
                # get rid of padded zeros
                self.data = filtered_trace

                self.setProvenance(
                    "highpass_filter",
                    {
                        "filter_type": "Butterworth gmprocess",
                        "filter_order": corners,
                        "number_of_passes": number_of_passes,
                        "corner_frequency": freq,
                    },
                )

        return self

    def getProvenanceKeys(self):
        """Get a list of all available provenance keys.

        Returns:
            list: List of available provenance keys.
        """
        if not len(self.provenance):
            return []
        pkeys = []
        for provdict in self.provenance:
            pkeys.append(provdict["prov_id"])
        return pkeys

    def getProvenance(self, prov_id):
        """Get seis-prov compatible attributes whose id matches prov_id.

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
            if provdict["prov_id"] == prov_id:
                matching_prov.append(provdict["prov_attributes"])
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
        provdict = {"prov_id": prov_id, "prov_attributes": prov_attributes}
        self.provenance.append(provdict)
        if "output_units" in prov_attributes.keys():
            self.stats.standard.units = prov_attributes["output_units"]
            try:
                self.stats.standard.units_type = REVERSE_UNITS[
                    prov_attributes["output_units"]
                ]
            except BaseException:
                self.stats.standard.units_type = "unknown"
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

    def getProvenanceDocument(self, base_prov=None, gmprocess_version="unknown"):
        """Generate a provenance document.

        Args:
            gmprocess_version (str):
                gmprocess version string.
            base_prov:
                Base provenance document.
        Returns:
            Provenance document.
        """
        if base_prov is None:
            pr = prov.model.ProvDocument()
            pr.add_namespace(*NS_SEIS)
            pr = _get_person_agent(pr)
            pr = _get_software_agent(pr, gmprocess_version)
            pr = _get_waveform_entity(self, pr)
        else:
            pr = _get_waveform_entity(self, copy.deepcopy(base_prov))
        sequence = 1
        for provdict in self.getAllProvenance():
            provid = provdict["prov_id"]
            prov_attributes = provdict["prov_attributes"]
            if provid not in ACTIVITIES:
                fmt = "Unknown or invalid processing parameter %s"
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
            parts = ident.split("_")
            sptype = parts[1]
            # hashid = '_'.join(parts[2:])
            # sp, sptype, hashid = ident.split('_')
            if sptype == "sa":
                for attr_key, attr_val in record.attributes:
                    key = attr_key.localpart
                    if isinstance(attr_val, prov.identifier.Identifier):
                        attr_val = attr_val.uri
                    software[key] = attr_val
            elif sptype == "pp":
                for attr_key, attr_val in record.attributes:
                    key = attr_key.localpart
                    if isinstance(attr_val, prov.identifier.Identifier):
                        attr_val = attr_val.uri
                    person[key] = attr_val
            elif sptype == "wf":  # waveform tag
                continue
            else:  # these are processing steps
                params = {}
                sptype = ""
                for attr_key, attr_val in record.attributes:
                    key = attr_key.localpart
                    if key == "label":
                        continue
                    elif key == "type":
                        _, sptype = attr_val.split(":")
                        continue
                    if isinstance(attr_val, datetime):
                        attr_val = UTCDateTime(attr_val)
                    params[key] = attr_val
                self.setProvenance(sptype, params)

            self.setParameter("software", software)
            self.setParameter("user", person)

    def hasParameter(self, param_id):
        """Check to see if Trace contains a given parameter.

        Args:
            param_id (str): Name of parameter to check.

        Returns:
            bool: True if parameter is set, False if not.
        """
        return param_id in self.parameters

    def setParameter(self, param_id, param_attributes):
        """Add to the StationTrace's set of arbitrary metadata.

        Args:
            param_id (str):
                Key for parameters dictionary.
            param_attributes (dict or list):
                Parameters for the given key.
        """
        self.parameters[param_id] = param_attributes

    def setCached(self, name, array_dict):
        """Store a dictionary of arrays in StationTrace.

        Args:
            name (str):
                Name of data dictionary to be stored.
            array_dict (dict):
                Dictionary with:
                    - key array name
                    - value as numpy array
        """
        self.cached[name] = array_dict

    def getCached(self, name):
        """Retrieve a dictionary of arrays.

        Args:
            name (str):
                Name of dictionary to retrieve.
        Returns:
            dict: Dictionary of arrays (see setSpectrum).
        """
        if name not in self.cached:
            raise KeyError(f"{name} not in set of spectra arrays.")
        return self.cached[name]

    def hasCached(self, name):
        """Check if StationTrace has cached attribute."""
        if name not in self.cached:
            return False
        return True

    def getCachedNames(self):
        """Return list of arrays that have been cached.

        Returns:
            list: List of cached arrays in this StationTrace.
        """
        return list(self.cached.keys())

    def getParameterKeys(self):
        """Get a list of all available parameter keys.

        Returns:
            list: List of available parameter keys.
        """
        return list(self.parameters.keys())

    def getParameter(self, param_id):
        """Retrieve some arbitrary metadata.

        Args:
            param_id (str):
                Key for parameters dictionary.

        Returns:
            dict or list:
                Parameters for the given key.
        """
        if param_id not in self.parameters:
            raise KeyError(f"Parameter {param_id} not found in StationTrace")
        return self.parameters[param_id]

    def getProvDataFrame(self):
        columns = ["Process Step", "Process Attribute", "Process Value"]
        df = pd.DataFrame(columns=columns)
        values = []
        attributes = []
        steps = []
        indices = []
        index = 0
        for activity in self.getAllProvenance():
            provid = activity["prov_id"]
            provstep = ACTIVITIES[provid]["label"]
            prov_attrs = activity["prov_attributes"]
            steps += [provstep] * len(prov_attrs)
            indices += [index] * len(prov_attrs)
            for key, value in prov_attrs.items():
                attributes.append(key)
                if isinstance(value, UTCDateTime):
                    value = value.datetime.strftime("%Y-%m-%d %H:%M:%S")
                values.append(str(value))
            index += 1

        mdict = {
            "Index": indices,
            "Process Step": steps,
            "Process Attribute": attributes,
            "Process Value": values,
        }
        df = pd.DataFrame(mdict)
        return df

    def getProvSeries(self):
        """Return a pandas Series containing the processing history for the
        trace.

        BO.NGNH31.HN2   Remove Response   input_units   counts
        -                                 output_units  cm/s^2
        -               Taper             side          both
        -                                 window_type   Hann
        -                                 taper_width   0.05

        Returns:
            Series:
                Pandas Series (see above).
        """
        tpl = (self.stats.network, self.stats.station, self.stats.channel)
        recstr = "%s.%s.%s" % tpl
        values = []
        attributes = []
        steps = []
        for activity in self.getAllProvenance():
            provid = activity["prov_id"]
            provstep = ACTIVITIES[provid]["label"]
            prov_attrs = activity["prov_attributes"]
            steps += [provstep] * len(prov_attrs)
            for key, value in prov_attrs.items():
                attributes.append(key)
                values.append(str(value))
        records = [recstr] * len(attributes)
        index = [records, steps, attributes]
        row = pd.Series(values, index=index)
        return row

    def __str__(self, id_length=None, indent=0):
        """
        Extends Trace __str__.
        """
        # set fixed id width

        if id_length:
            out = "%%-%ds" % (id_length)
            trace_id = out % self.id
        else:
            trace_id = f"{self.id}"
        out = ""
        # output depending on delta or sampling rate bigger than one
        if self.stats.sampling_rate < 0.1:
            if hasattr(self.stats, "preview") and self.stats.preview:
                out = (
                    out + " | "
                    "%(starttime)s - %(endtime)s | "
                    + "%(delta).1f s, %(npts)d samples [preview]"
                )
            else:
                out = (
                    out + " | "
                    "%(starttime)s - %(endtime)s | " + "%(delta).1f s, %(npts)d samples"
                )
        else:
            if hasattr(self.stats, "preview") and self.stats.preview:
                out = (
                    out + " | "
                    "%(starttime)s - %(endtime)s | "
                    + "%(sampling_rate).1f Hz, %(npts)d samples [preview]"
                )
            else:
                out = (
                    out + " | "
                    "%(starttime)s - %(endtime)s | "
                    + "%(sampling_rate).1f Hz, %(npts)d samples"
                )
        # check for masked array
        if np.ma.count_masked(self.data):
            out += " (masked)"
        if self.hasParameter("failure"):
            out += " (failed)"
        else:
            out += " (passed)"
        ind_str = " " * indent
        return ind_str + trace_id + out % (self.stats)


def _stats_from_inventory(data, inventory, seed_id, start_time):
    if len(inventory.source):
        if inventory.sender is not None and inventory.sender != inventory.source:
            source = f"{inventory.source},{inventory.sender}"
        else:
            source = inventory.source

    network_code, station_code, location_code, channel_code = seed_id.split(".")

    selected_inventory = inventory.select(
        network=network_code,
        station=station_code,
        location=location_code,
        channel=channel_code,
        time=start_time,
    )

    station = selected_inventory.networks[0].stations[0]
    channel = station.channels[0]

    coords = {
        "latitude": channel.latitude,
        "longitude": channel.longitude,
        "elevation": channel.elevation,
    }

    standard = {}

    # things we'll never get from an inventory object
    standard["corner_frequency"] = np.nan
    standard["instrument_damping"] = np.nan
    standard["instrument_period"] = np.nan
    standard["structure_type"] = ""
    standard["process_time"] = ""

    if data.dtype in INT_TYPES:
        standard["process_level"] = "raw counts"
    else:
        standard["process_level"] = "uncorrected physical units"

    standard["source"] = source
    standard["source_file"] = ""
    standard["instrument"] = ""
    standard["sensor_serial_number"] = ""
    if channel.sensor is not None:
        standard["instrument"] = "%s %s %s %s" % (
            channel.sensor.type,
            channel.sensor.manufacturer,
            channel.sensor.model,
            channel.sensor.description,
        )
        if channel.sensor.serial_number is not None:
            standard["sensor_serial_number"] = channel.sensor.serial_number
        else:
            standard["sensor_serial_number"] = ""

    if channel.azimuth is not None:
        standard["horizontal_orientation"] = channel.azimuth
    else:
        standard["horizontal_orientation"] = np.nan

    if channel.dip is not None:
        # Note: vertical orientatin is defined here as angle from horizontal
        standard["vertical_orientation"] = channel.dip
    else:
        standard["vertical_orientation"] = np.nan

    # if "units_type" not in standard.keys() or standard["units_type"] == "":
    #     standard["units_type"] = get_units_type(channel_code)
    # print(f"Stationtrace.py line 761: {standard['units_type']}")
    if len(channel.comments):
        comments = " ".join(
            channel.comments[i].value for i in range(len(channel.comments))
        )
        standard["comments"] = comments
    else:
        standard["comments"] = ""
    standard["station_name"] = ""
    if station.site.name != "None":
        standard["station_name"] = station.site.name
    # extract the remaining standard info and format_specific info
    # from a JSON string in the station description.

    format_specific = {}
    if station.description is not None and station.description != "None":
        jsonstr = station.description
        try:
            big_dict = json.loads(jsonstr)
            standard.update(big_dict["standard"])
            format_specific = big_dict["format_specific"]
        except json.decoder.JSONDecodeError:
            format_specific["description"] = jsonstr

    if "source_format" not in standard or standard["source_format"] is None:
        standard["source_format"] = "fdsn"

    standard["instrument_sensitivity"] = np.nan
    standard["volts_to_counts"] = np.nan
    response = None
    if channel.response is not None:
        response = channel.response
        if hasattr(response, "instrument_sensitivity"):
            units = response.instrument_sensitivity.input_units
            if "/" in units:
                num, denom = units.split("/")
                if num.lower() not in LENGTH_CONVERSIONS:
                    raise KeyError(
                        f"Sensitivity input units of {units} are not supported."
                    )
                conversion = LENGTH_CONVERSIONS[num.lower()]
                sensitivity = response.instrument_sensitivity.value * conversion
                response.instrument_sensitivity.value = sensitivity
                standard["instrument_sensitivity"] = sensitivity
                # find the volts to counts stage and store that
                if hasattr(response, "response_stages"):
                    for stage in response.response_stages:
                        if stage.input_units == "V" and stage.output_units == "COUNTS":
                            standard["volts_to_counts"] = stage.stage_gain
                            break
            else:
                standard[
                    "instrument_sensitivity"
                ] = response.instrument_sensitivity.value

    return (response, standard, coords, format_specific)


def _stats_from_header(header, config):
    if "_format" in header and header._format.lower() == "sac":
        # The plan is to add separate if blocks to support the different
        # formats as we encounter them here. See the SAC header documentation
        # here:
        # http://ds.iris.edu/files/sac-manual/manual/file_format.html

        # Todo: add support for SAC with PZ file.

        coords = {
            "latitude": header["sac"]["stla"],
            "longitude": header["sac"]["stlo"],
            "elevation": header["sac"]["stel"],
        }
        standard = {}
        standard["corner_frequency"] = np.nan
        standard["instrument_damping"] = np.nan
        standard["instrument_period"] = np.nan
        standard["structure_type"] = ""
        standard["process_time"] = ""
        standard["process_level"] = "uncorrected physical units"
        standard["source"] = config["read"]["sac_source"]
        standard["source_file"] = ""
        standard["instrument"] = ""
        standard["sensor_serial_number"] = ""
        standard["horizontal_orientation"] = float(header["sac"]["cmpaz"])
        # Note: vertical orientatin is defined here as angle from horizontal
        standard["vertical_orientation"] = 90.0 - float(header["sac"]["cmpinc"])
        if "units_type" not in standard.keys() or standard["units_type"] == "":
            utype = get_units_type(header["channel"])
            standard["units_type"] = utype
            standard["units"] = UNITS[utype]
        print(f"Stationtrace.py line 844: {standard['units_type']}")
        standard["comments"] = ""
        standard["station_name"] = ""
        standard["station_name"] = header["station"]
        format_specific = {
            "conversion_factor": float(config["read"]["sac_conversion_factor"])
        }
        standard["source_format"] = header._format
        standard["instrument_sensitivity"] = np.nan
        standard["volts_to_counts"] = np.nan
        response = None
    else:
        raise Exception("Format unsuppored without StationXML file.")

    return (response, standard, coords, format_specific)


def _get_software_agent(pr, gmprocess_version):
    """Get the seis-prov entity for the gmprocess software.

    Args:
        pr (prov.model.ProvDocument):
            Existing ProvDocument.
        gmprocess_version (str):
            gmprocess version.

    Returns:
        prov.model.ProvDocument:
            Provenance document updated with gmprocess software name/version.
    """
    software = "gmprocess"
    hashstr = "0000001"
    agent_id = f"seis_prov:sp001_sa_{hashstr}"
    giturl = "https://github.com/usgs/groundmotion-processing"
    pr.agent(
        agent_id,
        other_attributes=(
            (
                ("prov:label", software),
                (
                    "prov:type",
                    prov.identifier.QualifiedName(prov.constants.PROV, "SoftwareAgent"),
                ),
                ("seis_prov:software_name", software),
                ("seis_prov:software_version", gmprocess_version),
                (
                    "seis_prov:website",
                    prov.model.Literal(giturl, prov.constants.XSD_ANYURI),
                ),
            )
        ),
    )
    return pr


def _get_person_agent(pr, config=None):
    """Get the seis-prov entity for the user software.

    Args:
        pr (prov.model.ProvDocument):
            Existing ProvDocument.
        config (dict):
            Configuration options.

    Returns:
        prov.model.ProvDocument:
            Provenance document updated with gmprocess software name/version.
    """
    username = getpass.getuser()
    if config is None:
        config = get_config()
    fullname = ""
    email = ""
    if "user" in config:
        if "name" in config["user"]:
            fullname = config["user"]["name"]
        if "email" in config["user"]:
            email = config["user"]["email"]
    hashstr = "0000001"
    person_id = f"seis_prov:sp001_pp_{hashstr}"
    pr.agent(
        person_id,
        other_attributes=(
            (
                ("prov:label", username),
                (
                    "prov:type",
                    prov.identifier.QualifiedName(prov.constants.PROV, "Person"),
                ),
                ("seis_prov:name", fullname),
                ("seis_prov:email", email),
            )
        ),
    )
    return pr


def _get_waveform_entity(trace, pr):
    """Get the seis-prov entity for an input Trace.

    Args:
        trace (Trace):
            Input Obspy Trace object.
        pr (Prov):
            prov.model.ProvDocument

    Returns:
        prov.model.ProvDocument:
            Provenance document updated with waveform entity information.
    """
    tpl = (
        trace.stats.network.lower(),
        trace.stats.station.lower(),
        trace.stats.channel.lower(),
    )
    waveform_hash = "%s_%s_%s" % tpl
    waveform_id = f"seis_prov:sp001_wf_{waveform_hash}"
    pr.entity(
        waveform_id,
        other_attributes=(
            (
                ("prov:label", "Waveform Trace"),
                ("prov:type", "seis_prov:waveform_trace"),
            )
        ),
    )
    return pr


def _get_activity(pr, activity, attributes, sequence):
    """Get the seis-prov entity for an input processing "activity".

    See
    http://seismicdata.github.io/SEIS-PROV/_generated_details.html#activities

    for details on the types of activities that are possible to capture.


    Args:
        pr (prov.model.ProvDocument):
            Existing ProvDocument.
        activity (str):
            The prov:id for the input activity.
        attributes (dict):
            The attributes associated with the activity.
        sequence (int):
            Integer used to identify the order in which the activities were
            performed.
    Returns:
        prov.model.ProvDocument:
            Provenance document updated with input activity.
    """
    activity_dict = ACTIVITIES[activity]
    hashid = "%07i" % sequence
    code = activity_dict["code"]
    label = activity_dict["label"]
    activity_id = "sp%03i_%s_%s" % (sequence, code, hashid)
    pr_attributes = [("prov:label", label), ("prov:type", f"seis_prov:{activity}")]
    for key, value in attributes.items():
        if isinstance(value, float):
            value = prov.model.Literal(value, prov.constants.XSD_DOUBLE)
        elif isinstance(value, int):
            value = prov.model.Literal(value, prov.constants.XSD_INT)
        elif isinstance(value, UTCDateTime):
            value = prov.model.Literal(
                value.strftime(TIMEFMT), prov.constants.XSD_DATETIME
            )

        att_tuple = (f"seis_prov:{key}", value)
        pr_attributes.append(att_tuple)
    pr.activity(f"seis_prov:{activity_id}", other_attributes=pr_attributes)
    return pr
