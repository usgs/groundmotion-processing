#!/usr/bin/env python

# stdlib imports
import os
import numpy as np
import pkg_resources

# local imports
from gmprocess.metrics.rotation.rotation import Rotation
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.stationstream import StationStream
from gmprocess.stationtrace import StationTrace

ddir = os.path.join('data', 'testdata', 'process')
datadir = pkg_resources.resource_filename('gmprocess', ddir)


def test_rotation():

    # Create a stream and station summary, convert from m/s^2 to cm/s^2 (GAL)
    osc1_data = np.genfromtxt(datadir + '/ALCTENE.UW..sac.acc.final.txt')
    osc2_data = np.genfromtxt(datadir + '/ALCTENN.UW..sac.acc.final.txt')
    osc1_data = osc1_data.T[1] * 100
    osc2_data = osc2_data.T[1] * 100

    tr1 = StationTrace(data=osc1_data, header={'channel': 'HN1', 'delta': 0.01,
                                               'npts': len(osc1_data),
                                               'standard': {'corner_frequency': np.nan,
                                                            'station_name': '',
                                                            'source': 'json',
                                                            'instrument': '',
                                                            'instrument_period': np.nan,
                                                            'source_format': 'json',
                                                            'comments': '',
                                                            'structure_type': '',
                                                            'sensor_serial_number': '',
                                                            'process_level': 'raw counts',
                                                            'process_time': '',
                                                            'source_file': '',
                                                            'horizontal_orientation': np.nan,
                                                            'units': 'acc',
                                                            'units_type': 'acc,',
                                                            'instrument_sensitivity': np.nan,
                                                            'instrument_damping': np.nan}})
    tr2 = StationTrace(data=osc2_data, header={'channel': 'HN2', 'delta': 0.01,
                                               'npts': len(osc2_data),
                                               'standard': {'corner_frequency': np.nan,
                                                            'station_name': '',
                                                            'source': 'json',
                                                            'instrument': '',
                                                            'instrument_period': np.nan,
                                                            'source_format': 'json',
                                                            'comments': '',
                                                            'source_file': '',
                                                            'structure_type': '',
                                                            'sensor_serial_number': '',
                                                            'process_level': 'raw counts',
                                                            'process_time': '',
                                                            'horizontal_orientation': np.nan,
                                                            'units': 'acc',
                                                            'units_type': 'acc',
                                                            'instrument_sensitivity': np.nan,
                                                            'instrument_damping': np.nan}})
    st = StationStream([tr1, tr2])

    rotation_class = Rotation(st)

    # Test that GM, AM, and MAX work as expected with simple 1D datasets
    osc1 = np.asarray([0.0, 1.0, 2.0, 3.0])
    osc2 = np.asarray([4.0, 5.0, 6.0, 7.0])

    max_gm = rotation_class.get_max(osc1, 'gm', osc2)
    np.testing.assert_allclose(max_gm, 4.5826, atol=0.0001)

    max_am = rotation_class.get_max(osc1, 'am', osc2)
    np.testing.assert_allclose(max_am, 5.0, atol=0.0001)

    max_max = rotation_class.get_max(osc1, 'max', osc2)
    np.testing.assert_allclose(max_max, 7.0, atol=0.0001)

    # Test max for 1 1d Array
    osc1 = np.array([0.0, 1.0, 2.0])
    max_val = rotation_class.get_max(osc1, 'max')
    assert max_val == 2.0

    # Test arithmetic mean with 2D input
    osc1 = np.array([[0.0, 1.0], [2.0, 3.0]])
    osc2 = np.array([[4.0, 5.0], [6.0, 7.0]])
    means = rotation_class.get_max(osc1, 'am', osc2)[0]
    assert (means[0] == 3.0 and means[1] == 5.0)

    # Test greater of two horizontals
    maxs = rotation_class.get_max(osc1, 'max', osc2)[0]
    assert (maxs[0] == 5.0 and maxs[1] == 7.0)

    # Invalid dimensions
    osc1 = np.zeros((2, 3, 2))
    try:
        rotation_class.get_max(osc1, 'gm')
        success = True
    except Exception:
        success = False
    assert success is False

    # dimensions don't match
    osc1 = np.array([1.0, 2.0])
    osc2 = np.array([[1.0, 2.0], [3.0, 4.0]])
    try:
        rotation_class.get_max(osc1, 'gm', osc2)
        success = True
    except Exception:
        success = False
    assert success is False

    # Both invalid dimensions
    osc1 = np.zeros((2, 3, 2))
    osc2 = np.zeros((2, 3, 2))
    try:
        rotation_class.get_max(osc1, 'gm', osc2)
        success = True
    except Exception:
        success = False
    assert success is False

    # Invalid method pick
    try:
        osc1 = np.array([0.0, 1.0, 2.0])
        rotation_class.get_max(osc1, 'foo')
        success = True
    except Exception:
        success = False
    assert success is False


if __name__ == '__main__':
    test_rotation()
