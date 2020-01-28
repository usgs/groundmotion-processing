#!/usr/bin/env python

# stdlib imports
import os.path
import json

# third party imports
import numpy as np
import pkg_resources

# local imports
from gmprocess.io.read import read_data
from gmprocess.io.test_utils import read_data_dir
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.stationstream import StationStream
from gmprocess.stationtrace import StationTrace


def test_arias():
    ddir = os.path.join('data', 'testdata')
    datadir = pkg_resources.resource_filename('gmprocess', ddir)
    data_file = os.path.join(datadir, 'arias_data.json')
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
        'channel': 'HN1',
        'standard': {
            'corner_frequency': np.nan,
            'station_name': '',
            'source': 'json',
            'source_file': '',
            'instrument': '',
            'instrument_period': np.nan,
            'source_format': 'json',
            'comments': '',
            'structure_type': '',
            'sensor_serial_number': '',
            'process_level': 'raw counts',
            'process_time': '',
            'horizontal_orientation': np.nan,
            'units': 'acc',
            'units_type': 'acc',
            'instrument_sensitivity': np.nan,
            'instrument_damping': np.nan
        }
    }
    # input is cm/s/s output is m/s/s
    trace = StationTrace(data=acc * 100, header=header)
    trace2 = trace.copy()
    trace2.stats.channel = 'HN2'
    stream = StationStream([trace, trace2])

    for tr in stream:
        response = {'input_units': 'counts', 'output_units': 'cm/s^2'}
        tr.setProvenance('remove_response', response)

    station = StationSummary.from_stream(
        stream, ['ARITHMETIC_MEAN'], ['arias'])
    pgms = station.pgms
    Ia = pgms.loc['ARIAS', 'ARITHMETIC_MEAN'].Result
    # the target has only one decimal place and is in cm/s/s
    Ia = Ia * 100
    np.testing.assert_almost_equal(Ia, target_IA, decimal=1)

    # Test other components
    data_files, _ = read_data_dir('cwb', 'us1000chhc', '2-ECU.dat')
    stream = read_data(data_files[0])[0]
    station = StationSummary.from_stream(
        stream, [
            'channels', 'gmrotd', 'rotd50',
            'greater_of_two_horizontals', 'ARITHMETIC_MEAN'],
        ['arias']
    )
    stream = StationSummary.from_stream(stream, ['gmrotd50'], ['arias'])
    assert stream.pgms.Result.tolist() == []


if __name__ == '__main__':
    test_arias()
