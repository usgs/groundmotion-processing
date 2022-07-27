#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Methods for handling instrument response.
"""

import numpy as np
import logging
from gmprocess.core.stationtrace import PROCESS_LEVELS
from gmprocess.waveform_processing.processing_step import ProcessingStep

ABBREV_UNITS = {"ACC": "cm/s^2", "VEL": "cm/s", "DISP": "cm"}
M_TO_CM = 100.0


@ProcessingStep
def remove_response(
    st,
    pre_filt=True,
    f1=0.001,
    f2=0.005,
    f3=None,
    f4=None,
    water_level=60,
    inv=None,
    config=None,
):
    """
    Performs instrument response correction. If the response information is
    not already attached to the stream, then an inventory object must be
    provided. If the instrument is a strong-motion accelerometer, then
    tr.remove_sensitivity() will be used. High-gain seismometers will use
    tr.remove_response() with the defined pre-filter and water level.

    If f3 is Null it will be set to 0.9*fn, if f4 is Null it will be set to fn.

    Args:
        st (StationStream):
            Stream of data.
        pre_filt (bool):
            Apply a bandpass filter in frequency domain to the data before
            deconvolution?
        f1 (float):
            Frequency 1 for pre-filter.
        f2 (float):
            Frequency 2 for pre-filter.
        f3 (float):
            Frequency 3 for pre-filter.
        f4 (float):
            Frequency 4 for pre-filter.
        water_level (float):
            Water level for deconvolution.
        inv (obspy.core.inventory.inventory):
            Obspy inventory object containing response information.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Instrument-response-corrected stream.
    """
    output = "ACC"

    if inv is None:
        inv = st.getInventory()

    # Check if the response information is already attached in the trace stats
    for tr in st:

        # Check if this trace has already been converted to physical units
        if "remove_response" in tr.getProvenanceKeys():
            logging.debug(
                "Trace has already had instrument response removed. "
                "Nothing to be done."
            )
            continue

        f_n = 0.5 / tr.stats.delta
        if f3 is None:
            f3 = 0.9 * f_n
        if f4 is None:
            f4 = f_n
        if pre_filt:
            pre_filt_selected = (f1, f2, f3, f4)
        else:
            pre_filt_selected = None
        try:
            resp = inv.get_response(tr.id, tr.stats.starttime)
            paz = resp.get_paz()
            # Check if we have an instrument measuring velocity or accleration
            if tr.stats.channel[1] == "H":
                # Attempting to remove instrument response can cause a variety
                # errors due to bad response metadata
                try:
                    # Note: rater than set output to 'ACC' we are are setting
                    # it to 'VEl" and then differentiating.
                    tr.remove_response(
                        inventory=inv,
                        output="VEL",
                        water_level=water_level,
                        pre_filt=pre_filt_selected,
                        zero_mean=True,
                        taper=False,
                    )
                    tr.setProvenance(
                        "remove_response",
                        {
                            "method": "remove_response",
                            "input_units": "counts",
                            "output_units": ABBREV_UNITS["VEL"],
                            "water_level": water_level,
                            "pre_filt_freqs": str(pre_filt_selected),
                        },
                    )
                    diff_conf = config["differentiation"]
                    tr.differentiate(frequency=diff_conf["frequency"])
                    tr.data *= M_TO_CM  # Convert from m to cm
                    tr.stats.standard.units = ABBREV_UNITS[output]
                    tr.stats.standard.units_type = output.lower()
                    tr.stats.standard.process_level = PROCESS_LEVELS["V1"]
                except BaseException as e:
                    reason = (
                        "Encountered an error when attempting to remove "
                        "instrument response: %s" % str(e)
                    )
                    tr.fail(reason)
                    continue

                # Response removal can also result in NaN values due to bad
                # metadata, so check that data contains no NaN or inf values
                if not np.isfinite(tr.data).all():
                    reason = (
                        "Non-finite values encountered after removing "
                        "instrument response."
                    )
                    tr.fail(reason)
                    continue

            elif tr.stats.channel[1] == "N":
                try:
                    # If no poles and zeros are present in the xml file,
                    # use the sensitivity method.
                    if len(paz.poles) == 0 and len(paz.zeros) == 0:
                        tr.remove_sensitivity(inventory=inv)
                        tr.data *= M_TO_CM  # Convert from m to cm
                        tr.setProvenance(
                            "remove_response",
                            {
                                "method": "remove_sensitivity",
                                "input_units": "counts",
                                "output_units": ABBREV_UNITS[output],
                            },
                        )
                        tr.stats.standard.units = ABBREV_UNITS[output]
                        tr.stats.standard.units_type = output.lower()
                        tr.stats.standard.process_level = PROCESS_LEVELS["V1"]
                    else:
                        tr.remove_response(
                            inventory=inv,
                            output=output,
                            water_level=water_level,
                            pre_filt=pre_filt_selected,
                            zero_mean=True,
                            taper=False,
                        )
                        tr.data *= M_TO_CM  # Convert from m to cm
                        tr.setProvenance(
                            "remove_response",
                            {
                                "method": "remove_response",
                                "input_units": "counts",
                                "output_units": ABBREV_UNITS[output],
                                "water_level": water_level,
                                "pre_filt_freqs": str(pre_filt_selected),
                            },
                        )
                        tr.stats.standard.units = ABBREV_UNITS[output]
                        tr.stats.standard.units_type = output.lower()
                        tr.stats.standard.process_level = PROCESS_LEVELS["V1"]
                except BaseException as e:
                    reason = (
                        "Encountered an error when attempting to remove "
                        "instrument sensitivity: %s" % str(e)
                    )
                    tr.fail(reason)
                    continue
            else:
                reason = (
                    "This instrument type is not supported. "
                    "The instrument code must be either H "
                    "(high gain seismometer) or N (accelerometer)."
                )
                tr.fail(reason)
        except BaseException as e:
            logging.info(
                "Encountered an error when obtaining the poles and "
                "zeros information: %s. Now using remove_sensitivity "
                "instead of remove_response." % str(e)
            )
            tr.remove_sensitivity(inventory=inv)
            tr.data *= M_TO_CM  # Convert from m to cm
            tr.setProvenance(
                "remove_response",
                {
                    "method": "remove_sensitivity",
                    "input_units": "counts",
                    "output_units": ABBREV_UNITS[output],
                },
            )
            tr.stats.standard.units = ABBREV_UNITS[output]
            tr.stats.standard.units_type = output.lower()
            tr.stats.standard.process_level = PROCESS_LEVELS["V1"]

    return st
