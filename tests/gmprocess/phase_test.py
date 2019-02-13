#!/usr/bin/env python

from gmprocess.phase import PowerPicker
from obspy import read
import os

homedir = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(homedir, '..', 'data', 'process')


def test_p_pick():

    # Load some data

    # Run the P-Picker

    # Test against known values
    pass


if __name__ == '__main__':
    test_p_pick()
