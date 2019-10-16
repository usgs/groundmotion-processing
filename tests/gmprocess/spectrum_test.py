#!/usr/bin/env python

import os
import pkg_resources

import numpy as np

from gmprocess import spectrum
from gmprocess.streamcollection import StreamCollection
from gmprocess.config import get_config
from gmprocess.event import get_event_object
from gmprocess.windows import signal_split, signal_end
from gmprocess.snr import compute_snr
from gmprocess.processing import get_corner_frequencies


def test_fit_spectra():
    config = get_config()
    datapath = os.path.join('data', 'testdata', 'demo', 'ci38457511', 'raw')
    datadir = pkg_resources.resource_filename('gmprocess', datapath)
    event = get_event_object('ci38457511')
    sc = StreamCollection.from_directory(datadir)
    for st in sc:
        st = signal_split(st, event)
        end_conf = config['windows']['signal_end']
        st = signal_end(
            st,
            event_time=event.time,
            event_lon=event.longitude,
            event_lat=event.latitude,
            event_mag=event.magnitude,
            **end_conf
        )
        st = compute_snr(st, 30)
        st = get_corner_frequencies(
            st, method='constant',
            constant={
                'highpass': 0.08,
                'lowpass': 20.0
            }
        )

    for st in sc:
        spectrum.fit_spectra(st, event)


def test_spectrum():
    freq = np.logspace(-2, 2, 101)
    moment = spectrum.moment_from_magnitude(6.7)
    mod = spectrum.model((moment, 150), freq, 10, kappa=0.035)
    np.testing.assert_allclose(mod[0], 0.21764373, atol=1e-5)
    np.testing.assert_allclose(mod[50], 113.5025146, atol=1e-5)
    np.testing.assert_allclose(mod[-1], 0.0032295, atol=1e-5)


def test_fff():
    mags = np.linspace(3, 8, 51)
    h = [spectrum.finite_fault_factor(m) for m in mags]
    np.testing.assert_allclose(h[0], 0.37134706, atol=1e-5)
    np.testing.assert_allclose(h[30], 7.18762019, atol=1e-5)
    np.testing.assert_allclose(h[-1], 29.844204, atol=1e-5)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_fit_spectra()
    test_spectrum()
    test_fff()
