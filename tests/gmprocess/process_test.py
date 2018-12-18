#!/usr/bin/env python

# stdlib imports
import os.path
import numpy as np

# third party imports
from obspy.core.stream import read
from obspy.core.utcdatetime import UTCDateTime
from obspy import Trace

# local imports
from gmprocess import process

homedir = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(homedir, '..', 'data', 'process')


def test_amp_check_trim():

    # read the two sac files for testing
    # one is unedited with a standard maximum amplitude
    # the second has been multiplied so that it fails the amplitude check
    NOWS_tr = read(os.path.join(datadir, 'NOWSENR.sac'))[0]
    NOWS_tr_mul = Trace(data=NOWS_tr.data*10e9, header=NOWS_tr.stats)

    assert process.check_max_amplitude(NOWS_tr) is True
    assert process.check_max_amplitude(NOWS_tr_mul) is False

    # Check that our trim and window function doesn't affect the ending time
    # of this record
    org_time = UTCDateTime('2001-02-14T22:03:58')
    trim = process.trim_total_window(NOWS_tr, org_time, 32.7195).stats.endtime
    assert NOWS_tr.stats.endtime == trim


def test_corner_freqs():

    event_time = UTCDateTime('2001-02-28T18:54:32')
    ALCT_tr = read(os.path.join(datadir, 'ALCTENE.UW..sac'))[0]
    ALCT_dist = 75.9559

    corners_1 = process.get_corner_frequencies(ALCT_tr, event_time, ALCT_dist)
    np.testing.assert_allclose(corners_1, [0.036, 50.0], atol=0.001)

    ALCT_tr.stats.starttime += 300
    corners_2 = process.get_corner_frequencies(ALCT_tr, event_time, ALCT_dist)
    assert corners_2 == [-1, -1]

    event_time = UTCDateTime('2016-10-22T17:17:05')
    ALKI_tr = read(os.path.join(datadir, 'ALKIENE.UW..sac'))[0]
    ALKI_dist = 37.87883
    corners_3 = process.get_corner_frequencies(ALKI_tr, event_time, ALKI_dist,
                                               ratio=100000.0)
    assert corners_3 == [-2, -2]
    corners_4 = process.get_corner_frequencies(ALKI_tr, event_time, ALKI_dist)
    assert corners_4 == [-3, -3]


def test_all():
    config = {
        'processing_parameters': {
            'amplitude': {
                'min': 10e-7,
                'max': 5e3
            },
            'window': {
                'vmin': 1.0
            },
            'taper': {
                'type': 'hann',
                'max_percentage': 0.05,
                'side': 'both'
            },
            'corners': {
                'get_dynamically': True,
                'sn_ratio': 3.0,
                'max_low_freq': 0.1,
                'min_high_freq': 5.0,
                'default_low_frequency': 0.1,
                'default_high_frequency': 20.0
            },
            'filters': [{
                'type': 'highpass',
                'corners': 4,
                'zerophase': True
            }, {
                'type': 'lowpass',
                'corners': 4,
                'zerophase': True
            }],
            'baseline_correct': True,
        },
        'sm2xml': {
            'imtlist': ['PGA', 'PGV', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)']
        }
    }
    # Get our data directory
    event_time = UTCDateTime('2003-01-15T03:41:58')
    HAWA_dist = 80.1893
    HAWA_tr = read(os.path.join(datadir, 'HAWABHN.US..sac'))[0]
    HAWA_processed = process.process_config([HAWA_tr], config=config,
                                            event_time=event_time, epi_dist=HAWA_dist)[0]
    # Load in the already calculated array form processing
    HAWA_array = np.genfromtxt(os.path.join(datadir,
                                            'HAWABHN.US..sac.acc.final.txt'),
                               dtype=float)
    HAWA_array = HAWA_array.T
    HAWA_calc_data = HAWA_array[1]

    # Compare the processing script with the already processed data
    np.testing.assert_allclose(HAWA_processed.data, HAWA_calc_data, atol=0.001)

    # Test file that will conduct low-pass filter
    event_time = UTCDateTime('2001-02-28T18:54:32')
    BRI_dist = 55.6385
    BRI_tr = read(os.path.join(datadir, 'BRIHN1.GS..sac'))[0]
    BRI_processed = process.process_config([BRI_tr], config=config,
                                           event_time=event_time, epi_dist=BRI_dist)[0]
    assert BRI_processed.stats['passed_tests'] is True

    # Triggers the invalid low pass filtering warning
    event_time = UTCDateTime('2001-02-28T18:54:32')
    ALCT_dist = 75.9559
    ALCT_tr = read(os.path.join(datadir, 'ALCTENE.UW..sac'))[0]
    ALCT_processed = process.process_config([ALCT_tr], config=config,
                                            event_time=event_time, epi_dist=ALCT_dist)[0]
    assert ALCT_processed.stats['passed_tests'] is True

    GNW_tr = read(os.path.join(datadir, 'GNWBHE.UW..sac'))[0]
    GNW_dist = 46.7473
    GNW_processed = process.process_config([GNW_tr], config=config,
                                           event_time=event_time, epi_dist=GNW_dist)[0]
    assert GNW_processed.stats['passed_tests'] is True

    # Test trace with invalid amplitudes
    NOWS_tr_mul = read(os.path.join(datadir, 'NOWSENR_mul.sac'))[0]
    NOWS_tr_mul.data = NOWS_tr_mul.data * 100
    time = UTCDateTime('2001-02-14T22:03:58')
    dist = 50.05
    NOWS_processed = process.process_config([NOWS_tr_mul], config=config,
                                            event_time=time, epi_dist=dist)[0]
    assert NOWS_processed.stats['passed_tests'] is False

    # Test trace with low S/N ratio
    event_time = UTCDateTime('2016-10-22T17:17:05')
    ALKI_tr = read(os.path.join(datadir, 'ALKIENE.UW..sac'))[0]
    ALKI_dist = 37.87883
    ALKI_processed = process.process_config([ALKI_tr], config=config,
                                            event_time=event_time, epi_dist=ALKI_dist)[0]
    assert ALKI_processed.stats.processing_parameters.corners['default_low_frequency'] == 0.1
    assert ALKI_processed.stats.processing_parameters.corners['default_high_frequency'] == 20.0

    # Test with invalid starttime
    ALKI_tr.stats.starttime += 500
    ALKI_processed = process.process_config([ALKI_tr], config=config,
                                            event_time=event_time, epi_dist=ALKI_dist)[0]
    assert ALKI_processed.stats['passed_tests'] is False

    ALKI_split = process.split_signal_and_noise(ALKI_tr, event_time, ALKI_dist)
    assert ALKI_split == (-1, -1)

    config = {
        'processing_parameters': {
            'amplitude': {
                'min': 10e-7,
                'max': 5e3
            },
            'window': {
                'vmin': 1.0
            },
            'taper': {
                'type': 'hann',
                'max_percentage': 0.05,
                        'side': 'both'
            },
            'corners': {
                'get_dynamically': False,
                'sn_ratio': 3.0,
                'max_low_freq': 0.1,
                'min_high_freq': 5.0,
                'default_low_frequency': 0.1,
                'default_high_frequency': 20.0
            },
            'filters': [{
                'type': 'highpass',
                        'corners': 4,
                        'zerophase': True
            }, {
                'type': 'lowpass',
                        'corners': 4,
                        'zerophase': True
            }, {
                'type': 'bandpass',
                'corners': 4,
                'zerophase': True
            }, {
                'type': 'invalid',
                'corners': 4,
                'zerophase': True
            }],
            'baseline_correct': False,
        },
        'sm2xml': {
            'imtlist': ['PGA', 'PGV', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)']
        }
    }
    ALKI_processed = process.process_config([ALKI_tr], config=config)[0]
    assert ALKI_processed.stats['passed_tests'] is False
    ALKI_processed = process.process_config([ALKI_tr])[0]
    assert ALKI_processed.stats['passed_tests'] is False


def test_horizontal_frequencies():
    config = {
        'processing_parameters': {
            'amplitude': {
                'min': 10e-7,
                'max': 5e3
            },
            'window': {
                'vmin': 1.0
            },
            'taper': {
                'type': 'hann',
                'max_percentage': 0.05,
                'side': 'both'
            },
            'corners': {
                'get_dynamically': True,
                'sn_ratio': 3.0,
                'max_low_freq': 0.1,
                'min_high_freq': 5.0,
                'default_low_frequency': 0.1,
                'default_high_frequency': 20.0
            },
            'filters': [{
                'type': 'highpass',
                'corners': 4,
                'zerophase': True
            }, {
                'type': 'lowpass',
                'corners': 4,
                'zerophase': True
            }],
            'baseline_correct': True,
        },
        'sm2xml': {
            'imtlist': ['PGA', 'PGV', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)']
        }
    }
    event_time = UTCDateTime('2001-02-28T18:54:32')
    ALCT_tr1 = read(os.path.join(datadir, 'ALCTENE.UW..sac'))[0]
    ALCT_tr2 = read(os.path.join(datadir, 'ALCTENN.UW..sac'))[0]
    stream = [ALCT_tr1, ALCT_tr2]

    ALCT_dist = 75.9559
    processed = process.process_config(stream, config=config,
                                       event_time=event_time, epi_dist=ALCT_dist)
    for trace in processed:
        corners = trace.stats.processing_parameters.corners
        assert corners['default_high_frequency'] == 50
        assert corners['default_low_frequency'] == 0.018310546875
        filters = trace.stats.processing_parameters.filters
        assert filters == config['processing_parameters']['filters']

    stream[0].stats.channel = 'Z'
    processed = process.process_config(stream, config=config,
                                       event_time=event_time, epi_dist=ALCT_dist)
    corners1 = processed[0].stats.processing_parameters.corners
    high1 = corners1['default_high_frequency']
    low1 = corners1['default_low_frequency']
    assert high1 == 50.0
    assert low1 == 0.0244140625
    corners2 = processed[1].stats.processing_parameters.corners
    high2 = corners2['default_high_frequency']
    low2 = corners2['default_low_frequency']
    assert high2 == 48.4619140625
    assert low2 == 0.018310546875


if __name__ == '__main__':
    test_amp_check_trim()
    test_corner_freqs()
    test_all()
    test_horizontal_frequencies()
