#!/usr/bin/env python

# stdlib imports
import os
import numpy as np
import pkg_resources

# local imports
from obspy.core.stream import Stream
from obspy.core.trace import Trace
from gmprocess.metrics.rotation import get_max, rotate
from gmprocess.metrics.station_summary import StationSummary

ddir = os.path.join('data', 'testdata', 'process')
datadir = pkg_resources.resource_filename('gmprocess', ddir)


def test_rotation():

    # Create a stream and station summary, convert from m/s^2 to cm/s^2 (GAL)
    osc1_data = np.genfromtxt(datadir + '/ALCTENE.UW..sac.acc.final.txt')
    osc2_data = np.genfromtxt(datadir + '/ALCTENN.UW..sac.acc.final.txt')
    osc1_data = osc1_data.T[1] * 100
    osc2_data = osc2_data.T[1] * 100

    tr1 = Trace(data=osc1_data, header={'channel': 'H1', 'delta': 0.01,
                                        'npts': 10400})
    tr2 = Trace(data=osc2_data, header={'channel': 'H2', 'delta': 0.01,
                                        'npts': 10400})
    st = Stream([tr1, tr2])

    imts = ['PGA', 'PGV', 'SA0.3', 'SA1.0', 'SA3.0']
    station = StationSummary.from_stream(st, ['channels', 'rotd'], imts)

    # Get PGA and spectral accelerations
    st_PGA = station.oscillators['PGA']
    pgv = station.oscillators['PGV']
    st_SA10 = station.oscillators['SA(1.0)_ROT']
    st_SA30 = station.oscillators['SA(3.0)_ROT']
    st_SA03 = station.oscillators['SA(0.3)_ROT']

    rot_st_PGA = rotate(st_PGA[0], st_PGA[1], combine=True)
    rot_PGV = rotate(pgv[0], pgv[1], combine=True)

    max50_pgv = (get_max(rot_PGV, 'max', percentiles=[50]))[1]
    max50_pga = (get_max(rot_st_PGA, 'max', percentiles=[50]))[1]
    max50_SA10 = (get_max(st_SA10[0], 'max', percentiles=[50]))[1]
    max50_SA03 = (get_max(st_SA03[0], 'max', percentiles=[50]))[1]
    max50_SA30 = (get_max(st_SA30[0], 'max', percentiles=[50]))[1]

    # Check the calculations
    np.testing.assert_allclose(max50_pga, 4.12528265306, atol=0.1)
    np.testing.assert_allclose(max50_SA10, 10.7362857143, atol=0.1)
    np.testing.assert_allclose(max50_pgv, 6.239364, atol=0.1)
    np.testing.assert_allclose(max50_SA03, 10.1434159021, atol=0.1)
    np.testing.assert_allclose(max50_SA30, 1.12614169215, atol=0.1)

    # Test that GM, AM, and MAX work as expected with simple 1D datasets
    osc1 = np.asarray([0.0, 1.0, 2.0, 3.0])
    osc2 = np.asarray([4.0, 5.0, 6.0, 7.0])

    max_gm = get_max(osc1, 'gm', osc2)
    np.testing.assert_allclose(max_gm, 4.5826, atol=0.0001)

    max_am = get_max(osc1, 'am', osc2)
    np.testing.assert_allclose(max_am, 5.0, atol=0.0001)

    max_max = get_max(osc1, 'max', osc2)
    np.testing.assert_allclose(max_max, 7.0, atol=0.0001)

    # Test max for 1 1d Array
    osc1 = np.array([0.0, 1.0, 2.0])
    max_val = get_max(osc1, 'max')
    assert max_val == 2.0

    # Test arithmetic mean with 2D input
    osc1 = np.array([[0.0, 1.0], [2.0, 3.0]])
    osc2 = np.array([[4.0, 5.0], [6.0, 7.0]])
    means = get_max(osc1, 'am', osc2)[0]
    assert (means[0] == 3.0 and means[1] == 5.0)

    # Test greater of two horizontals
    maxs = get_max(osc1, 'max', osc2)[0]
    assert (maxs[0] == 5.0 and maxs[1] == 7.0)


def test_exceptions():

    # Invalid dimensions
    osc1 = np.zeros((2, 3, 2))
    try:
        get_max(osc1, 'gm')
        success = True
    except Exception:
        success = False
    assert success is False

    # dimensions don't match
    osc1 = np.array([1.0, 2.0])
    osc2 = np.array([[1.0, 2.0], [3.0, 4.0]])
    try:
        get_max(osc1, 'gm', osc2)
        success = True
    except Exception:
        success = False
    assert success is False

    # Both invalid dimensions
    osc1 = np.zeros((2, 3, 2))
    osc2 = np.zeros((2, 3, 2))
    try:
        get_max(osc1, 'gm', osc2)
        success = True
    except Exception:
        success = False
    assert success is False

    # Invalid method pick
    try:
        osc1 = np.array([0.0, 1.0, 2.0])
        get_max(osc1, 'foo')
        success = True
    except Exception:
        success = False
    assert success is False


if __name__ == '__main__':
    test_rotation()
    test_exceptions()
