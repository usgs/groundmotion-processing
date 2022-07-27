#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from gmprocess.utils.config import get_config
from gmprocess.waveform_processing.filtering import (
    lowpass_filter_trace,
    highpass_filter_trace,
)
from gmprocess.waveform_processing.baseline_correction import correct_baseline
from gmprocess.waveform_processing.integrate import get_disp
from gmprocess.waveform_processing.processing_step import ProcessingStep


@ProcessingStep
def adjust_highpass_corner(
    st,
    step_factor=1.5,
    maximum_freq=0.5,
    max_final_displacement=0.2,
    max_displacment_ratio=0.2,
    config=None,
):
    """Adjust high pass corner frequency.

    Options for further refinement of the highpass corner. Currently, this
    includes criteria employed by:

        Dawood, H.M., Rodriguez-Marek, A., Bayless, J., Goulet, C. and
        Thompson, E. (2016). A flatfile for the KiK-net database processed
        using an automated protocol. Earthquake Spectra, 32(2), pp.1281-1302.

    This algorithm begins with an initial corner frequency that was selected
    as configured in the `get_corner_frequencies` step. It then chcks the
    criteria descibed below; if the criteria are not met then the high pass
    corner is increased the multiplicative step factor until the criteria
    are met.

    Args:
        st (StationStream):
            Stream of data.
        step_factor (float):
            Multiplicative factor for incrementing high pass corner.
        maximum_freq (float):
            Limit (maximum) frequency on the trial corner frequencies
            to search across to pass displacement checks.
        max_final_displacement (float):
            Maximum allowable value (in cm) for final displacement.
        max_displacment_ratio (float):
            Maximum allowable ratio of final displacement to max displacment.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream.

    """

    for tr in st:
        if not tr.hasParameter("corner_frequencies"):
            tr.fail(
                "Cannot apply adjust_highpass_corner method because "
                "initial corner frequencies are not set."
            )
        else:
            initial_corners = tr.getParameter("corner_frequencies")
            f_hp = initial_corners["highpass"]
            ok = __disp_checks(
                tr, max_final_displacement, max_displacment_ratio, config
            )
            while not ok:
                f_hp = step_factor * f_hp
                if f_hp > maximum_freq:
                    tr.fail(
                        "Could not pass adjust_highpass_corner checks "
                        "for f_hp below maximum_freq."
                    )
                    break
                initial_corners["highpass"] = f_hp
                tr.setParameter("corner_frequencies", initial_corners)
                ok = __disp_checks(
                    tr, max_final_displacement, max_displacment_ratio, config
                )
    return st


def __disp_checks(
    tr, max_final_displacement=0.025, max_displacment_ratio=0.2, config=None
):
    # Need to find the high/low pass filtering steps in the config
    # to ensure that filtering here is done with the same options
    if config is None:
        config = get_config()
    processing_steps = config["processing"]
    ps_names = [list(ps.keys())[0] for ps in processing_steps]
    ind = int(np.where(np.array(ps_names) == "highpass_filter")[0][0])
    hp_args = processing_steps[ind]["highpass_filter"]
    ind = int(np.where(np.array(ps_names) == "lowpass_filter")[0][0])
    lp_args = processing_steps[ind]["lowpass_filter"]

    # Make a copy of the trace so we don't modify it in place with
    # filtering or integration
    trdis = tr.copy()

    # Filter
    trdis = lowpass_filter_trace(trdis, **lp_args)
    trdis = highpass_filter_trace(trdis, **hp_args)

    # Apply baseline correction
    trdis = correct_baseline(trdis, config)

    # Integrate to displacment
    trdis = get_disp(trdis, config=config)

    # Checks
    ok = True
    max_displacment = np.max(np.abs(trdis.data))
    final_displacement = np.abs(trdis.data[-1])
    disp_ratio = final_displacement / max_displacment

    if final_displacement > max_final_displacement:
        ok = False

    if disp_ratio > max_displacment_ratio:
        ok = False

    return ok
