#!/usr/bin/env python

# stdlib imports
import os

# third party imports
import numpy as np
import scipy.constants as sp
from obspy import read, read_inventory
from obspy.geodetics import gps2dist_azimuth
from obspy.core.event import Origin

# local imports
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.metrics.exception import PGMException

homedir = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(homedir, '..', '..', 'data', 'fdsnfetch')


def test_radial_transverse():

    origin = Origin(latitude=47.149, longitude=-122.7266667)
    st = read(os.path.join(datadir, 'resp_cor', 'UW.ALCT.--.*.MSEED'))

    st[0].stats.standard = {}
    st[0].stats.standard['horizontal_orientation'] = 0
    st[1].stats.standard = {}
    st[1].stats.standard['horizontal_orientation'] = 90

    inv = read_inventory(os.path.join(datadir, 'inventory.xml'))
    stalat, stalon = inv[0][0][0].latitude, inv[0][0][0].longitude

    for tr in st:
        tr.stats['coordinates'] = {'latitude': stalat}
        tr.stats['coordinates']['longitude'] = stalon

    baz = gps2dist_azimuth(stalat, stalon,
                           origin.latitude, origin.longitude)[1]

    st1 = st.copy()
    st1[0].stats.channel = st1[0].stats.channel[:-1] + 'N'
    st1[1].stats.channel = st1[1].stats.channel[:-1] + 'E'
    st1.rotate(method='NE->RT', back_azimuth=baz)
    pgms = np.abs(st1.max())

    st2 = st.copy()

    summary = StationSummary.from_stream(
        st2, ['radial_transverse'], ['pga'], origin)

    np.testing.assert_almost_equal(
        pgms[0], sp.g * summary.pgms['PGA']['RADIAL_TRANSVERSE']['R'])

    np.testing.assert_almost_equal(
        pgms[1], sp.g * summary.pgms['PGA']['RADIAL_TRANSVERSE']['T'])

    # Test with a station whose channels are not aligned to E-N
    SEW_st = read(os.path.join(datadir, 'resp_cor', 'GS.SEW.*.mseed'))
    SEW_inv = read_inventory(os.path.join(datadir, 'inventory_sew.xml'))
    stalat, stalon = inv[0][0][0].latitude, inv[0][0][0].longitude

    for tr in SEW_st:
        tr.stats.standard = \
            {'horizontal_orientation':
             SEW_inv.get_channel_metadata(tr.get_id())['azimuth']}
        tr.stats.coordinates = {'latitude': stalat,
                                'longitude': stalon}
    baz = gps2dist_azimuth(stalat, stalon,
                           origin.latitude, origin.longitude)[1]

    SEW_st_copy = SEW_st.copy()

    SEW_st_copy.rotate(method='->ZNE', inventory=SEW_inv)
    SEW_st_copy.rotate(method='NE->RT', back_azimuth=baz)
    pgms = np.abs(SEW_st_copy.max())

    summary = StationSummary.from_stream(
        SEW_st, ['radial_transverse'], ['pga'], origin)

    np.testing.assert_almost_equal(
        pgms[1], sp.g * summary.pgms['PGA']['RADIAL_TRANSVERSE']['R'])

    np.testing.assert_almost_equal(
        pgms[2], sp.g * summary.pgms['PGA']['RADIAL_TRANSVERSE']['T'])

    # Test failure case without two horizontal channels
    copy1 = st.copy()
    copy1[0].stats.channel = copy1[0].stats.channel[:-1] + '3'
    success = False
    try:
        StationSummary.from_stream(
            copy1, ['radial_transverse'], ['pga'], origin)
        success = True
    except PGMException:
        success = False
    assert success is False

    # Test failure case when traces are different lengths
    copy2 = st.copy()
    copy2[0].trim(endtime=copy2[0].stats.endtime - 1)
    try:
        StationSummary.from_stream(
            copy2, ['radial_transverse'], ['pga'], origin, )
        success = True
    except PGMException:
        success = False
    assert success is False

    # Test failure case when channels are not orthogonal
    copy3 = st.copy()
    copy3[0].stats.standard.horizontal_orientation = 100
    try:
        StationSummary.from_stream(
            copy3, ['radial_transverse'], ['pga'], origin)
        success = True
    except PGMException:
        success = False
    assert success is False


if __name__ == '__main__':
    test_radial_transverse()
