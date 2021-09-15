#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from gmprocess.io.read import read_data
from gmprocess.io.test_utils import read_data_dir
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.clipping.max_amp import Max_Amp


def test_max_calc():
    data_files, _ = read_data_dir('clipping_samples', 'hv70907436', '*.mseed')
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    st_max_amps = []
    for st in sc:
        max_amp_method = Max_Amp(st)
        st_max_amps.append(max_amp_method.max_amp)

    np.testing.assert_allclose(
        st_max_amps,
        np.array([8435914.830898283,
                  11525175.173268152,
                  10090978.868285095,
                  8553230.5231931563,
                  8509963.5836342424,
                  8122003.3022054331]),
        rtol=1e-5
    )


def test_all_max_calc():
    data_files, _ = read_data_dir('clipping_samples', 'hv70907436', '*.mseed')
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    st_max_amps = []
    for st in sc:
        max_amp_method = Max_Amp(st, test_all=True)
        st_max_amps.append(max_amp_method.max_amp)

    np.testing.assert_allclose(
        st_max_amps,
        np.array([[8435914.830898283, 8204508.3222043216, 8698976.5524693076],
                  [11525175.173268152, 8496598.1711016055, 8766397.4644186441],
                  [10090978.868285095, 8463705.7919004504, 8379389.0031664912],
                  [8553230.5231931563, 8344327.3850897169, 5621557.4998055659],
                  [8509963.5836342424, 10646801.251152713, 8805642.5964668635],
                  [8122003.3022054331, 8148959.0193878114, 8989844.6071329378]]),
        rtol=1e-5
    )


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_max_calc()
    test_all_max_calc()