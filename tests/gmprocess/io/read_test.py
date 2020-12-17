#!/usr/bin/env python

# stdlib imports
import os

from gmprocess.io.read import read_data, _get_format, _validate_format
from gmprocess.utils.exception import GMProcessException
from gmprocess.io.test_utils import read_data_dir


def test_read():
    cosmos_files, _ = read_data_dir('cosmos',
                                    'ci14155260',
                                    'Cosmos12TimeSeriesTest.v1')
    cwb_files, _ = read_data_dir('cwb',
                                 'us1000chhc',
                                 '1-EAS.dat')
    dmg_files, _ = read_data_dir('dmg',
                                 'nc71734741',
                                 'CE89146.V2')
    geonet_files, _ = read_data_dir('geonet',
                                    'us1000778i',
                                    '20161113_110259_WTMC_20.V1A')
    knet_files, _ = read_data_dir('knet',
                                  'us2000cnnl',
                                  'AOM0011801241951.EW')
    smc_files, _ = read_data_dir('smc',
                                 'nc216859',
                                 '0111a.smc')

    file_dict = {}
    file_dict['cosmos'] = cosmos_files[0]
    file_dict['cwb'] = cwb_files[0]
    file_dict['dmg'] = dmg_files[0]
    file_dict['geonet'] = geonet_files[0]
    file_dict['knet'] = knet_files[0]
    file_dict['smc'] = smc_files[0]

    for file_format in file_dict:
        file_path = file_dict[file_format]
        assert _get_format(file_path) == file_format
        assert _validate_format(file_path, file_format) == file_format

    assert _validate_format(file_dict['knet'], 'smc') == 'knet'
    assert _validate_format(file_dict['dmg'], 'cosmos') == 'dmg'
    assert _validate_format(file_dict['cosmos'], 'invalid') == 'cosmos'

    for file_format in file_dict:
        try:
            stream = read_data(file_dict[file_format], file_format)[0]
        except Exception as e:
            x = 1
        assert stream[0].stats.standard['source_format'] == file_format
        stream = read_data(file_dict[file_format])[0]
        assert stream[0].stats.standard['source_format'] == file_format
    # test exception
    try:
        file_path = smc_files[0].replace('0111a.smc', 'not_a_file.smc')
        read_data(file_path)[0]
        success = True
    except GMProcessException:
        success = False
    assert success == False


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_read()
