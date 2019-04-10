#!/usr/bin/env python
from gmprocess.phase import (PowerPicker, pphase_pick, pick_ar,
                             pick_kalkan, pick_power, pick_baer, pick_yeck)
from gmprocess.io.read import read_data
from gmprocess.io.test_utils import read_data_dir
from gmprocess.exception import GMProcessException
from gmprocess.config import get_config
from obspy import read, UTCDateTime
from obspy.core.trace import Trace
from obspy.core.stream import Stream
from scipy.io import loadmat
import numpy as np
import os
import pkg_resources
import matplotlib.pyplot as plt
import shutil
import pandas as pd
import time


def test_p_pick():
    datapath = os.path.join('data', 'testdata', 'process')
    datadir = pkg_resources.resource_filename('gmprocess', datapath)
    # Testing a strong motion channel
    tr = read(datadir + '/ALCTENE.UW..sac')[0]
    chosen_ppick = UTCDateTime('2001-02-28T18:54:47')
    ppick = PowerPicker(tr)
    ptime = tr.times('utcdatetime')[0] + ppick
    assert (abs(chosen_ppick - ptime)) < 0.2

    # Testing a broadband channel
    tr = read(datadir + '/HAWABHN.US..sac')[0]
    chosen_ppick = UTCDateTime('2003-01-15T03:42:12.5')
    ppick = PowerPicker(tr)
    ptime = tr.times('utcdatetime')[0] + ppick
    assert (abs(chosen_ppick - ptime)) < 0.2

    # Test a Northridge file that should fail to return a P-pick
    tr = read_data(datadir + '/017m30ah.m0a')[0][0]
    ppick = PowerPicker(tr)
    assert ppick == -1


def test_pphase_picker():
    # compare our results with a data file from E. Kalkan
    datapath = os.path.join('data', 'testdata', 'strong-motion.mat')
    datafile = pkg_resources.resource_filename('gmprocess', datapath)
    matlabfile = loadmat(datafile)
    x = np.squeeze(matlabfile['x'])

    dt = matlabfile['dt'][0][0]
    hdr = {'delta': dt,
           'sampling_rate': 1 / dt,
           'npts': len(x),
           'starttime': UTCDateTime('1970-01-01'),
           'standard': {'units': 'acc'}}
    trace = Trace(data=x, header=hdr)
    stream = Stream(traces=[trace])
    period = 0.01
    damping = 0.6
    nbins = 200
    loc = pphase_pick(stream[0], period=period, damping=damping,
                      nbins=nbins,
                      peak_selection=True)
    assert loc == 26.035


def test_all_pickers():
    streams = get_streams()
    picker_config = get_config(picker=True)
    methods = ['ar', 'baer', 'power', 'kalkan']
    columns = ['Stream', 'Method', 'Pick_Time', 'Mean_SNR']
    df = pd.DataFrame(columns=columns)
    for stream in streams:
        print(stream.get_id())
        for method in methods:
            t1 = time.time()
            try:
                if method == 'ar':
                    loc, mean_snr = pick_ar(
                        stream, picker_config=picker_config)
                elif method == 'baer':
                    loc, mean_snr = pick_baer(
                        stream, picker_config=picker_config)
                elif method == 'power':
                    loc, mean_snr = pick_power(
                        stream, picker_config=picker_config)
                elif method == 'kalkan':
                    loc, mean_snr = pick_kalkan(stream,
                                                picker_config=picker_config)
                elif method == 'yeck':
                    loc, mean_snr = pick_yeck(stream)
            except GMProcessException:
                loc = -1
                mean_snr = np.nan
            t2 = time.time()
            dt = t2 - t1
            row = {'Stream': stream.get_id(),
                   'Method': method,
                   'Pick_Time': loc,
                   'Mean_SNR': mean_snr}
            df = df.append(row, ignore_index=True)
        x = 1
    stations = df['Stream'].unique()
    cmpdict = {'TW.ECU.BN': 'kalkan',
               'TW.ELD.BN': 'power',
               'TW.EGF.BN': 'power',
               'TW.EAS.BN': 'power',
               'TW.EDH.BN': 'power',
               'TK.4304.HN': 'kalkan',
               'TK.0921.HN': 'baer',
               'TK.5405.HN': 'power',
               'NZ.HSES.HN': 'baer',
               'NZ.WTMC.HN': 'baer',
               'NZ.THZ.HN': 'power'}
    for station in stations:
        station_df = df[df['Stream'] == station]
        max_snr = station_df['Mean_SNR'].max()
        maxrow = station_df[station_df['Mean_SNR'] == max_snr].iloc[0]
        method = maxrow['Method']
        assert cmpdict[station] == method


def get_streams():
    datafiles1, origin1 = read_data_dir('cwb', 'us1000chhc', '*.dat')
    datafiles2, origin2 = read_data_dir('nsmn', 'us20009ynd', '*.txt')
    datafiles3, origin3 = read_data_dir('geonet', 'us1000778i', '*.V1A')
    datafiles = datafiles1 + datafiles2 + datafiles3
    streams = []
    for datafile in datafiles:
        streams += read_data(datafile)

    return streams


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_all_pickers()
    test_pphase_picker()
    test_p_pick()
