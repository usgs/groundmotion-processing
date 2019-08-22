#!/usr/bin/env python

# stdlib imports
import os

# third party imports
import vcr
import pkg_resources

# local imports
from gmprocess.io.catalog import convert_ids


def test_id_conversions():
    eventid = 'us10006g7d'
    target_ingv = '7073641'
    # target_dict = {
    #     'EMSC': '525580',
    #     'UNID': '20160824_0000006',
    #     'ISC': '611462212',
    #     'INGV': target_ingv
    # }
    # ISC event appears to have vanished from this webservice
    target_dict = {
        'EMSC': '525580',
        'UNID': '20160824_0000006',
        'INGV': target_ingv
    }
    datafile = os.path.join('data', 'testdata', 'vcr_catalog_test.yaml')
    tape_file = pkg_resources.resource_filename('gmprocess', datafile)
    with vcr.use_cassette(tape_file):

        ids_dict = convert_ids(eventid, 'USGS', ['INGV', 'EMSC', 'UNID'])
        assert ids_dict == target_dict

        new_id = convert_ids(eventid, 'USGS', 'INGV')
        assert new_id == target_ingv

        new_id = convert_ids(eventid, 'USGS', ['INGV'])
        assert new_id == target_ingv

        ids_dict = convert_ids(eventid, 'USGS', ['all'])
        assert ids_dict == target_dict

        ids_dict = convert_ids(eventid, 'USGS', 'all')
        assert ids_dict == target_dict

        ids_dict = convert_ids(target_ingv, 'INGV', 'all')
        del target_dict['INGV']
        target_dict['USGS'] = eventid
        assert ids_dict == target_dict

        try:
            convert_ids('invalid', 'USGS', 'all')
            success = True
        except Exception:
            success = False
        assert success is False

        try:
            convert_ids(eventid, 'invalid', 'all')
            success = True
        except Exception:
            success = False
        assert success is False

        try:
            convert_ids(eventid, 'USGS', 'unk')
            success = True
        except Exception:
            success = False
        assert success is False


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_id_conversions()
