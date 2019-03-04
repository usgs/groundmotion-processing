#!/usr/bin/env python

# stdlib imports
import os.path

from gmprocess.io.read import read_data, _get_format, _validate_format
from gmprocess.exception import GMProcessException


def test_read():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    cosmos_dir = os.path.join(
        homedir, '..', '..', 'data', 'cosmos', 'ci14155260')
    cwb_dir = os.path.join(homedir, '..', '..', 'data', 'cwb', 'us1000chhc')
    dmg_dir = os.path.join(homedir, '..', '..', 'data', 'dmg', 'nc71734741')
    geonet_dir = os.path.join(
        homedir, '..', '..', 'data', 'geonet', 'us1000778i')
    knet_dir = os.path.join(homedir, '..', '..', 'data', 'knet', 'us2000cnnl')
    smc_dir = os.path.join(homedir, '..', '..', 'data', 'smc', 'nc216859')
    file_dict = {}
    file_dict['cosmos'] = os.path.join(cosmos_dir, 'Cosmos12TimeSeriesTest.v1')
    file_dict['cwb'] = os.path.join(cwb_dir, '1-EAS.dat')
    file_dict['dmg'] = os.path.join(dmg_dir, 'CE89146.V2')
    file_dict['geonet'] = os.path.join(
        geonet_dir, '20161113_110259_WTMC_20.V1A')
    file_dict['knet'] = os.path.join(knet_dir, 'AOM0011801241951.EW')
    file_dict['smc'] = os.path.join(smc_dir, '0111a.smc')

    for file_format in file_dict:
        file_path = file_dict[file_format]
        assert _get_format(file_path) == file_format
        assert _validate_format(file_path, file_format) == file_format

    assert _validate_format(file_dict['knet'], 'smc') == 'knet'
    assert _validate_format(file_dict['dmg'], 'cosmos') == 'dmg'
    assert _validate_format(file_dict['cosmos'], 'invalid') == 'cosmos'

    for file_format in file_dict:
        stream = read_data(file_dict[file_format], file_format)[0]
        assert stream[0].stats.standard['source_format'] == file_format
        stream = read_data(file_dict[file_format])[0]
        assert stream[0].stats.standard['source_format'] == file_format
    # test exception
    try:
        file_path = os.path.join(smc_dir, 'not_a_file.smc')
        read_data(file_path)[0]
        success = True
    except GMProcessException:
        success = False
    assert success == False


if __name__ == '__main__':
    test_read()
