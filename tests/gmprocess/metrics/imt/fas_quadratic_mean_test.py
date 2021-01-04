#!/usr/bin/env python

# stdlib imports
import os.path
import re

# third party imports
import numpy as np
import pkg_resources

# Local imports
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace


def test_fas():
    """
    Testing based upon the work provided in
    https://github.com/arkottke/notebooks/blob/master/effective_amp_spectrum.ipynb
    """
    ddir = os.path.join('data', 'testdata')
    datadir = pkg_resources.resource_filename('gmprocess', ddir)
    fas_file = os.path.join(datadir, 'fas_quadratic_mean.txt')
    p1 = os.path.join(datadir, 'peer', 'RSN763_LOMAP_GIL067.AT2')
    p2 = os.path.join(datadir, 'peer', 'RSN763_LOMAP_GIL337.AT2')

    stream = StationStream([])
    for idx, fpath in enumerate([p1, p2]):
        with open(fpath, encoding='utf-8') as file_obj:
            for _ in range(3):
                next(file_obj)
            meta = re.findall(r'[.0-9]+', next(file_obj))
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
                'vertical_orientation': np.nan,
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
    summary = StationSummary.from_stream(
        stream, ['quadratic_mean'], imts, bandwidth=30)

    pgms = summary.pgms
    for idx, f in enumerate(freqs):
        fstr = 'FAS(%.3f)' % (1 / f)
        fval = pgms.loc[fstr, 'QUADRATIC_MEAN'].Result
        np.testing.assert_allclose(
            fval,
            fas[idx] * stream[0].stats.delta,
            rtol=1e-5,
            atol=1e-5
        )


if __name__ == '__main__':
    test_fas()
