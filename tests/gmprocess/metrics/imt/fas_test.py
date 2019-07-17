#!/usr/bin/env python

# stdlib imports
import os.path
import re

# third party imports
import numpy as np
import pkg_resources

# Local imports
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.stationstream import StationStream
from gmprocess.stationtrace import StationTrace


def test_fas():
    """
    Testing based upon the work provided in
    https://github.com/arkottke/notebooks/blob/master/effective_amp_spectrum.ipynb
    """
    ddir = os.path.join('data', 'testdata')
    datadir = pkg_resources.resource_filename('gmprocess', ddir)
    fas_file = os.path.join(datadir, 'fas_results.txt')
    p1 = os.path.join(datadir, 'peer', 'RSN763_LOMAP_GIL067.AT2')
    p2 = os.path.join(datadir, 'peer', 'RSN763_LOMAP_GIL337.AT2')

    stream = StationStream([])
    for idx, fpath in enumerate([p1, p2]):
        with open(fpath) as file_obj:
            for _ in range(3):
                next(file_obj)
            meta = re.findall(r'[.0-9]+', next(file_obj))
            count = int(meta[0])
            dt = float(meta[1])
            accels = np.array(
                [col for line in file_obj for col in line.split()])
        trace = StationTrace(data=accels, header={
            'channel': 'H' + str(idx),
            'delta': dt,
            'units': 'acc',
            'standard': {
                'corner_frequency': np.nan,
                'station_name': '',
                'source': 'json',
                'instrument': '',
                'instrument_period': np.nan,
                'source_format': 'json',
                'comments': '',
                'structure_type': '',
                'sensor_serial_number': '',
                'source_file': '',
                'process_level': 'raw counts',
                'process_time': '',
                'horizontal_orientation': np.nan,
                'units': 'acc',
                'units_type': 'acc',
                'instrument_sensitivity': np.nan,
                'instrument_damping': np.nan
            }
        })
        stream.append(trace)

    for tr in stream:
        response = {'input_units': 'counts', 'output_units': 'cm/s^2'}
        tr.setProvenance('remove_response', response)

    freqs, fas = np.loadtxt(fas_file, unpack=True,
                            usecols=(0, 1), delimiter=',')
    # scaling required on the test data as it was not accounted for originally
    imts = ['fas' + str(1 / p) for p in freqs]
    summary = StationSummary.from_stream(stream, ['quadratic_mean'], imts,
                                         bandwidth=30)

    pgms = summary.pgms
    for idx, f in enumerate(freqs):
        fstr = 'FAS(' + str(1 / f) + ')'
        fval = pgms[pgms.IMT == fstr].Result.tolist()[0]
        np.testing.assert_array_almost_equal(
            fval, fas[idx] / len(stream[0].data))

    # test exceptions
    failed = False
    try:
        fas_dict = calculate_fas(
            stream, '', 1 / freqs, 'some other smoothing', 30)
    except Exception as e:
        failed = True
    assert(failed == True)

    failed = False
    invalid_channels_stream = stream
    invalid_channels_stream[0].stats.channel = 'Z'
    try:
        fas_dict = calculate_fas(
            invalid_channels_stream, '', 1 / freqs, 'konno_ohmachi', 30)
    except Exception as e:
        failed = True
    assert(failed == True)

    failed = False
    invalid_units_stream = stream
    invalid_units_stream[0].stats.units = 'other'
    try:
        fas_dict = calculate_fas(
            invalid_units_stream,
            '', 1 / freqs, 'konno_ohmachi', 30)
    except Exception as e:
        failed = True
    assert(failed == True)


if __name__ == '__main__':
    test_fas()
