#!/usr/bin/env python

# stdlib imports
import os.path
import re

# third party imports
import numpy as np
from obspy.core.stream import Stream
from obspy.core.trace import Trace

# local imports
from gmprocess.metrics.imt.fas import calculate_fas


def test_fas():
    """
    Testing based upon the work provided in
    https://github.com/arkottke/notebooks/blob/master/effective_amp_spectrum.ipynb
    """
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    fas_file = os.path.join(homedir, '..', '..', 'data', 'fas_results.txt')
    p1 = os.path.join(homedir, '..', '..',
            'data', 'peer', 'RSN763_LOMAP_GIL067.AT2')
    p2 = os.path.join(homedir, '..', '..', 'data',
            'peer', 'RSN763_LOMAP_GIL337.AT2')

    stream = Stream()
    for idx, fpath in enumerate([p1, p2]):
        with open(fpath) as file_obj:
            for _ in range(3):
                next(file_obj)
            meta = re.findall(r'[.0-9]+', next(file_obj))
            count = int(meta[0])
            dt = float(meta[1])
            accels = np.array(
                    [col for line in file_obj for col in line.split()])
        trace = Trace(data=accels, header={
                'channel': 'H' + str(idx),
                'delta': dt,
                'units': 'g'})
        stream.append(trace)

    freqs, fas = np.loadtxt(fas_file, unpack=True, usecols=(0,1), delimiter=',')
    # scaling required on the test data as it was not accounted for originally
    fas_dict = calculate_fas(stream, '', 1 / freqs, 'konno_ohmachi', 30)
    for f in fas_dict:
        idx = np.argwhere(freqs == 1/f)
        np.testing.assert_array_almost_equal(fas_dict[f],fas[idx]/len(trace.data))

    # test exceptions
    failed = False
    try:
        fas_dict = calculate_fas(stream, '', 1 / freqs, 'some other smoothing', 30)
    except Exception as e:
        failed = True
    assert(failed == True)

    failed = False
    invalid_channels_stream = stream
    invalid_channels_stream[0].stats.channel = 'Z'
    try:
        fas_dict = calculate_fas(invalid_channels_stream, '', 1 / freqs, 'konno_ohmachi', 30)
    except Exception as e:
        failed = True
    assert(failed == True)

    failed = False
    invalid_units_stream = stream
    invalid_units_stream[0].stats.units = 'other'
    try:
        fas_dict = calculate_fas(invalid_units_stream, '', 1 / freqs, 'konno_ohmachi', 30)
    except Exception as e:
        failed = True
    assert(failed == True)


if __name__ == '__main__':
    test_fas()
