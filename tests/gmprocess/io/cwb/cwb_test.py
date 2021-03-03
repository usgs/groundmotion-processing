#!/usr/bin/env python

# stdlib imports
import os
import tempfile
import shutil

# third party imports
import numpy as np

# local imports
from gmprocess.io.cwb.core import is_cwb, read_cwb, _get_header_info
from gmprocess.io.test_utils import read_data_dir


def test():
    cwb_file, _ = read_data_dir('cwb', 'us1000chhc', files=['1-EAS.dat'])
    cwb_file = cwb_file[0]
    assert is_cwb(cwb_file)
    assert is_cwb(os.path.abspath(__file__)) is False
    stream = read_cwb(cwb_file)[0]
    np.testing.assert_almost_equal(
        np.abs(stream[0].max()), 0.83699999999999997)
    assert stream[0].stats['sampling_rate'] == 50

    cwb_file, _ = read_data_dir('cwb', 'us1000chhc', files=['2-ECU.dat'])
    cwb_file = cwb_file[0]
    assert is_cwb(cwb_file)
    assert is_cwb(os.path.abspath(__file__)) is False
    stream = read_cwb(cwb_file)[0]
    for trace in stream:
        stats = trace.stats
        assert stats['station'] == 'ECU'
        assert stats['sampling_rate'] == 50
        dt = '%Y-%m-%dT%H:%M:%SZ'
        assert stats['starttime'].strftime(dt) == '2018-02-06T15:50:29Z'
        assert stats.standard['station_name'] == 'Chulu'
        assert stats.standard['instrument'] == 'FBA'
        assert stats.coordinates['latitude'] == 22.860
        assert stats.coordinates['longitude'] == 121.092
        assert stats.format_specific['dc_offset_z'] == -1.017
        assert stats.format_specific['dc_offset_h1'] == -2.931
        assert stats.format_specific['dc_offset_h2'] == -2.811
        defaulted = ['instrument_period', 'instrument_damping',
                     'corner_frequency']
        for default in defaulted:
            assert str(stats.standard[default]) == 'nan'
        defaulted = ['comments', 'structure_type',
                     'sensor_serial_number', 'process_time']
        for default in defaulted:
            assert stats.standard[default] == ''
    # Test alternate defaults
    missing_info = """#Earthquake Information
    \n#Origin Time(GMT+08): 2018/02/06-23:50:42
    \n#EpicenterLongitude(E): 121.69
    \n#EpicenterLatitude(N): 24.14
    \n#Depth(km): 10.0
    \n#Magnitude(Ml): 6.0
    \n#Station Information
    \n#StationCode: ECU
    \n#StartTime(GMT+08): 2018/02/06-23:50:29.000
    \n#RecordLength(sec): 120
    \n#SampleRate(Hz): 50
    \n#AmplitudeUnit:  gal. DCoffset(corr)
    \n#DataSequence: Time U(+); N(+); E(+)
    \n#Data: 4F10.3
         0.000     0.000     0.000     0.000
         0.020     0.000     0.000     0.000
         0.040     0.000     0.000     0.000
         0.060     0.000     0.000     0.000
         0.080     0.000     0.000     0.000
         0.100     0.000     0.000     0.000
         0.120     0.000     0.000     0.000
            """
    data = stream[0].data
    data = np.reshape(data, (int(len(data) / 2), 2), order='C')
    temp_dir = tempfile.mkdtemp()
    try:
        tfile = os.path.join(temp_dir, 'tfile.txt')
        with open(tfile, "w", encoding='utf-8') as f:
            f.write(missing_info)
        metadata = _get_header_info(open(tfile, 'rt'), data)
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(temp_dir)

    assert str(metadata['coordinates']['longitude']) == 'nan'
    assert str(metadata['coordinates']['latitude']) == 'nan'
    assert metadata['standard']['station_name'] == ''
    assert metadata['standard']['instrument'] == ''
    assert str(metadata['format_specific']['dc_offset_z']) == 'nan'
    assert str(metadata['format_specific']['dc_offset_h2']) == 'nan'
    assert str(metadata['format_specific']['dc_offset_h1']) == 'nan'


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test()
