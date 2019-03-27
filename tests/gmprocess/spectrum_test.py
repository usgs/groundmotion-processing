#!/usr/bin/env python

import numpy as np
from gmprocess import spectrum


def test_spectrum():
    freq = np.logspace(-2, 2, 101)
    mod = spectrum.model(freq, 10, kappa=0.035, magnitude=6.7)
    np.testing.assert_allclose(mod[0], 0.21764373, atol=1e-5)
    np.testing.assert_allclose(mod[50], 113.234943, atol=1e-5)
    np.testing.assert_allclose(mod[-1], 0.00322216, atol=1e-5)


def test_fff():
    mags = np.linspace(3, 8, 51)
    h = [spectrum.finite_fault_factor(m) for m in mags]
    np.testing.assert_allclose(h[0], 0.37134706, atol=1e-5)
    np.testing.assert_allclose(h[30], 7.18762019, atol=1e-5)
    np.testing.assert_allclose(h[-1], 29.844204, atol=1e-5)


if __name__ == '__main__':
    test_spectrum()
    test_fff()
