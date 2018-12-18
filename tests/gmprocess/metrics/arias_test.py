#!/usr/bin/env python

# stdlib imports
import os.path
import json

# third party imports
from obspy.core.stream import Stream
from obspy.core.trace import Trace
import numpy as np

# local imports
from gmprocess.io.read import read_data
from gmprocess.metrics.imt.arias import calculate_arias
from gmprocess.metrics.station_summary import StationSummary


def test_arias():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    data_file = os.path.join(homedir, '..', '..', 'data',
                             'arias_data.json')
    with open(data_file, 'rt') as f:
        jdict = json.load(f)

    time = np.array(jdict['time'])
    # input output is m/s/s
    acc = np.array(jdict['acc']) / 100
    target_IA = jdict['ia']
    delta = time[2] - time[1]
    sr = 1 / delta
    header = {
        'delta': delta,
        'sampling_rate': sr,
        'npts': len(acc),
        'units': 'm/s/s',
        'channel': 'H1'
    }
    trace = Trace(data=acc, header=header)
    stream = Stream([trace])
    Ia = calculate_arias(stream, ['channels'])['H1']
    # the target has only one decimal place and is in cm/s/s
    Ia = Ia * 100
    np.testing.assert_almost_equal(Ia, target_IA, decimal=1)

    # input is cm/s/s output is m/s/s
    trace = Trace(data=acc * 100, header=header)
    stream = Stream([trace])
    station = StationSummary.from_stream(stream, ['channels'], ['arias'])
    Ia = station.pgms['ARIAS']['H1']
    # the target has only one decimal place and is in cm/s/s
    Ia = Ia * 100
    np.testing.assert_almost_equal(Ia, target_IA, decimal=1)

    # Test other components
    data_file = os.path.join(homedir, '..', '..', 'data', 'cwb', '2-ECU.dat')
    stream = read_data(data_file)
    station = StationSummary.from_stream(stream,
                                         ['channels', 'gmrotd', 'rotd50',
                                             'greater_of_two_horizontals'],
                                         ['arias'])


def test_exceptions():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    data_file = os.path.join(homedir, '..', '..', 'data',
                             'arias_data.json')
    with open(data_file, 'rt') as f:
        jdict = json.load(f)

    time = np.array(jdict['time'])
    # input output is m/s/s
    acc = np.array(jdict['acc']) / 100
    delta = time[2] - time[1]
    sr = 1 / delta
    header = {
        'delta': delta,
        'sampling_rate': sr,
        'npts': len(acc),
        'units': 'm/s/s',
        'channel': 'H1'
    }
    trace = Trace(data=acc, header=header)
    stream = Stream([trace])
    try:
        StationSummary.from_stream(stream, ['gmrotd50'], ['arias'])
        sucess = True
    except:
        sucess = False
    assert sucess == False

    try:
        StationSummary.from_stream(stream, ['rotd50'], ['arias'])
        sucess = True
    except:
        sucess = False
    assert sucess == False


if __name__ == '__main__':
    test_arias()
    test_exceptions()
