#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import scipy.constants as sp
from obspy import read, read_inventory
from obspy.geodetics import gps2dist_azimuth
from obspy.core.event import Origin

from gmprocess.metrics.station_summary import StationSummary
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace
from gmprocess.utils.constants import DATA_DIR


datadir = DATA_DIR / "testdata" / "fdsnfetch"


def test_radial_transverse():

    origin = Origin(latitude=47.149, longitude=-122.7266667)
    st = read(datadir / "resp_cor" / "UW.ALCT.--.*.MSEED")

    st[0].stats.standard = {}
    st[0].stats.standard["horizontal_orientation"] = 0.0
    st[0].stats["channel"] = "HN1"
    st[1].stats.standard = {}
    st[1].stats.standard["horizontal_orientation"] = 90.0
    st[1].stats["channel"] = "HN2"
    st[2].stats.standard = {}
    st[2].stats.standard["horizontal_orientation"] = np.nan
    st[2].stats["channel"] = "HNZ"

    inv = read_inventory(datadir / "inventory.xml")
    stalat, stalon = inv[0][0][0].latitude, inv[0][0][0].longitude

    for i, tr in enumerate(st):
        tr.stats["coordinates"] = {"latitude": stalat}
        tr.stats["coordinates"]["longitude"] = stalon
        tr.stats["standard"].update(
            {
                "corner_frequency": np.nan,
                "station_name": "",
                "source": "json",
                "instrument": "",
                "instrument_period": np.nan,
                "vertical_orientation": np.nan,
                "source_format": "json",
                "comments": "",
                "structure_type": "",
                "source_file": "",
                "sensor_serial_number": "",
                "process_level": "raw counts",
                "process_time": "",
                "units": "cm/s/s",
                "units_type": "acc",
                "instrument_sensitivity": np.nan,
                "volts_to_counts": np.nan,
                "instrument_damping": np.nan,
            }
        )
    baz = gps2dist_azimuth(stalat, stalon, origin.latitude, origin.longitude)[1]

    st1 = st.copy()
    st1[0].stats.channel = st1[0].stats.channel[:-1] + "N"
    st1[1].stats.channel = st1[1].stats.channel[:-1] + "E"
    st1.rotate(method="NE->RT", back_azimuth=baz)
    pgms = np.abs(st1.max())

    st2 = StationStream([])
    for t in st:
        st2.append(StationTrace(t.data, t.stats))

    for tr in st2:
        response = {"input_units": "counts", "output_units": "cm/s^2"}
        tr.setProvenance("remove_response", response)

    summary = StationSummary.from_stream(st2, ["radial_transverse"], ["pga"], origin)
    pgmdf = summary.pgms
    R = pgmdf.loc["PGA", "HNR"].Result
    T = pgmdf.loc["PGA", "HNT"].Result
    np.testing.assert_almost_equal(pgms[0], sp.g * R)

    np.testing.assert_almost_equal(pgms[1], sp.g * T)

    # Test with a station whose channels are not aligned to E-N
    SEW_st = read(datadir / "resp_cor" / "GS.SEW.*.mseed")
    SEW_inv = read_inventory(datadir / "inventory_sew.xml")
    stalat, stalon = inv[0][0][0].latitude, inv[0][0][0].longitude

    # This needs to be checked. The target data doesn't appear to be
    # correct. This can be updated when a tolerance is added to the rotate
    # method.
    """traces = []
    for tr in SEW_st:
        tr.stats.coordinates = {'latitude': stalat,
                                'longitude': stalon}
        tr.stats.standard = {'corner_frequency': np.nan,
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
            'horizontal_orientation':
             SEW_inv.get_channel_metadata(tr.get_id())['azimuth'],
            'units': 'acc',
            'instrument_damping': np.nan}
        traces += [StationTrace(tr.data, tr.stats)]
    baz = gps2dist_azimuth(stalat, stalon,
                           origin.latitude, origin.longitude)[1]
    SEW_st_copy = StationStream(traces)
    SEW_st_copy.rotate(method='->NE', inventory=SEW_inv)
    SEW_st_copy.rotate(method='NE->RT', back_azimuth=baz)
    pgms = np.abs(SEW_st_copy.max())

    summary = StationSummary.from_stream(
        SEW_st, ['radial_transverse'], ['pga'], origin)

    np.testing.assert_almost_equal(
        pgms[1], sp.g * summary.pgms['PGA']['R'])

    np.testing.assert_almost_equal(
        pgms[2], sp.g * summary.pgms['PGA']['T'])"""

    # Test failure case without two horizontal channels
    copy1 = st2.copy()
    copy1[0].stats.channel = copy1[0].stats.channel[:-1] + "3"
    pgms = StationSummary.from_stream(
        copy1, ["radial_transverse"], ["pga"], origin
    ).pgms
    assert np.isnan(pgms.loc["PGA", "HNR"].Result)
    assert np.isnan(pgms.loc["PGA", "HNT"].Result)

    # Test failure case when channels are not orthogonal
    copy3 = st2.copy()
    copy3[0].stats.standard.horizontal_orientation = 100
    pgms = StationSummary.from_stream(
        copy3, ["radial_transverse"], ["pga"], origin
    ).pgms
    assert np.isnan(pgms.loc["PGA", "HNR"].Result)
    assert np.isnan(pgms.loc["PGA", "HNT"].Result)


if __name__ == "__main__":
    test_radial_transverse()
