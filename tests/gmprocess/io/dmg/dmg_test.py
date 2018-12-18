#!/usr/bin/env python

# stdlib imports
import os.path
import tempfile

# local imports
from gmprocess.exception import GMProcessException
from gmprocess.io.dmg.core import is_dmg, read_dmg


def test_dmg():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    datadir = os.path.join(homedir, '..', '..', '..', 'data', 'dmg')
    file1 = os.path.join(datadir, 'CE89146.V2')
    file2 = os.path.join(datadir, 'CIWLT.V2')
    file3 = os.path.join(datadir, 'CE58667.V2')

    for filename in [file1, file2]:
        assert is_dmg(file1)

        # test acceleration from the file
        stream1 = read_dmg(filename)

        # test for three traces
        assert stream1.count() == 3

        # test that the traces are acceleration
        for trace in stream1:
            assert trace.stats['standard']['units'] == 'acc'

        # test velocity from the file
        stream2 = read_dmg(filename, units='vel')

        # test for three traces
        assert stream2.count() == 3

        # test that the traces are velocity
        for trace in stream2:
            assert trace.stats['standard']['units'] == 'vel'

        # test displacement from the file
        stream3 = read_dmg(filename, units='disp')

        # test for three traces
        assert stream3.count() == 3

        # test that the traces are displacement
        for trace in stream3:
            assert trace.stats['standard']['units'] == 'disp'

    # Test metadata
    stream = read_dmg(file1)
    for trace in stream:
        stats = trace.stats
        assert stats['station'] == '89146'
        assert stats['delta'] == .005000
        assert stats['location'] == '--'
        assert stats['network'] == 'ZZ'
        dt = '%Y-%m-%dT%H:%M:%SZ'
        assert stats['starttime'].strftime(dt) == '2012-02-13T21:06:45Z'
        assert stats.coordinates['latitude'] == 40.941
        assert stats.coordinates['longitude'] == -123.633
        assert stats.standard['station_name'] == 'Willow Creek'
        assert stats.standard['instrument'] == 'Etna'
        assert stats.standard['sensor_serial_number'] == '2500'
        if stats['channel'] == 'H1':
            assert stats.format_specific['sensor_sensitivity'] == 629
            assert stats.standard['horizontal_orientation'] == 360
            assert stats.standard['instrument_period'] == .0108814
            assert stats.standard['instrument_damping'] == .6700000
        if stats['channel'] == 'H2':
            assert stats.standard['horizontal_orientation'] == 90
            assert stats.standard['instrument_period'] == .0100000
            assert stats.standard['instrument_damping'] == .6700000
        if stats['channel'] == 'Z':
            assert stats.standard['horizontal_orientation'] == 500
            assert stats.standard['instrument_period'] == .0102354
            assert stats.standard['instrument_damping'] == .6700000
        assert stats.standard['process_level'] == 'V2'
        assert stats.standard['source_format'] == 'dmg'
        assert stats.standard['source'] == ''
        assert str(stats.format_specific['time_sd']) == 'nan'
        assert stats.format_specific['scaling_factor'] == 980.665
        assert stats.format_specific['low_filter_corner'] == .3
        assert stats.format_specific['high_filter_corner'] == 40

    stream = read_dmg(file2)
    for trace in stream:
        stats = trace.stats
        assert stats['station'] == 'WLT'
        assert stats['delta'] == .0200000
        assert stats['location'] == '--'
        assert stats['network'] == 'CI'
        dt = '%Y-%m-%dT%H:%M:%SZ'
        assert stats['starttime'].strftime(dt) == '2014-03-29T04:09:34Z'
        assert stats.coordinates['latitude'] == 34.009
        assert stats.coordinates['longitude'] == -117.951
        assert stats.standard['station_name'] == 'Hacienda Heights'
        assert stats.standard['instrument'] == ''
        assert stats.standard['sensor_serial_number'] == '4310'
        assert stats.standard['source'] == 'Southern California Seismic ' + \
            'Network, California Institute of Technology (Caltech)'

    # test acceleration from the file
    stream3 = read_dmg(filename)
    assert len(stream3) == 3

    # Test for wrong format exception
    success = True
    try:
        datadir = os.path.join(homedir, '..', '..', '..', 'data', 'cwb')
        file3 = os.path.join(datadir, '1-EAS.dat')
        read_dmg(file3)
    except Exception:
        success = False
    assert success == False

    # Test for bad date in header warning
    try:
        datadir = os.path.join(homedir, '..', '..', '..', 'data', 'dmg')
        file4 = os.path.join(datadir, 'BadHeader.V2')
        read_dmg(file4)
    except Exception:
        success = False
    assert success == False
    # Test alternate defaults
    no_stream = """RESPONSE AND FOURIER AMPLITUDE SPECTRA
    CORRECTED ACCELEROGRAM
    UNCORRECTED ACCELEROGRAM DATA"""
    tmp = tempfile.NamedTemporaryFile(delete=True)
    with open(tmp.name, 'w') as f:
        f.write(no_stream)
    f = open(tmp.name, 'rt')
    try:
        read_dmg(tmp.name)
        success = True
    except GMProcessException:
        success = False
    assert success == False
    tmp.close()

    no_stream = """UNCORRECTED ACCELEROGRAM DATA"""
    tmp = tempfile.NamedTemporaryFile(delete=True)
    with open(tmp.name, 'w') as f:
        f.write(no_stream)
    f = open(tmp.name, 'rt')
    try:
        read_dmg(tmp.name)
        success = True
    except GMProcessException:
        success = False
    assert success == False
    tmp.close()

    # test location override
    stream = read_dmg(filename, location='test')
    for trace in stream:
        assert trace.stats.location == 'test'


if __name__ == '__main__':
    test_dmg()
