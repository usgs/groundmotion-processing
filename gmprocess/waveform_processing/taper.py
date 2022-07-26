#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gmprocess.waveform_processing.processing_step import ProcessingStep

TAPER_TYPES = {
    "cosine": "Cosine",
    "barthann": "Bartlett-Hann",
    "bartlett": "Bartlett",
    "blackman": "Blackman",
    "blackmanharris": "Blackman-Harris",
    "bohman": "Bohman",
    "boxcar": "Boxcar",
    "chebwin": "Dolph-Chebyshev",
    "flattop": "Flat top",
    "gaussian": "Gaussian",
    "general_gaussian": "Generalized Gaussian",
    "hamming": "Hamming",
    "hann": "Hann",
    "kaiser": "Kaiser",
    "nuttall": "Blackman-Harris according to Nuttall",
    "parzen": "Parzen",
    "slepian": "Slepian",
    "triang": "Triangular",
}


@ProcessingStep
def taper(st, type="hann", width=0.05, side="both", config=None):
    """
    Taper streams.

    Args:
        st (StationStream):
            Stream of data.
        type (str):
            Taper type.
        width (float):
            Taper width as percentage of trace length.
        side (str):
            Valid options: "both", "left", "right".
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        stream: tapered streams.
    """
    if not st.passed:
        return st

    for tr in st:
        tr.taper(max_percentage=width, type=type, side=side)
        window_type = TAPER_TYPES[type]
        tr.setProvenance(
            "taper", {"window_type": window_type, "taper_width": width, "side": side}
        )
    return st
