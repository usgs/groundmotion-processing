#!/usr/bin/env python

# stdlib imports
import os.path

# local imports
from gmprocess.io.cosmos.core import read_cosmos
from gmprocess.io.cwb.core import read_cwb
from gmprocess.io.dmg.core import read_dmg
from gmprocess.io.geonet.core import read_geonet
from gmprocess.io.knet.core import read_knet
from gmprocess.io.obspy.core import read_obspy
from gmprocess.io.smc.core import read_smc

REQUIRED = ['horizontal_orientation',
            'instrument_period',
            'instrument_damping',
            'process_time',
            'process_level',
            'station_name',
            'sensor_serial_number',
            'instrument',
            'comments',
            'structure_type',
            'corner_frequency',
            'units',
            'source',
            'source_format']


def test_smc():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    datadir = os.path.join(homedir, '..', '..', 'data')

    files = {'cosmos': (read_cosmos, 'Cosmos12TimeSeriesTest.v1'),
             'cwb': (read_cwb, '1-EAS.dat'),
             'dmg': (read_dmg, 'CE89146.V2'),
             'geonet': (read_geonet, '20161113_110259_WTMC_20.V1A'),
             'knet': (read_knet, 'AOM0011801241951.EW'),
             'obspy': (read_obspy, '51PJW_H1.mseed'),
             'smc': (read_smc, '0111a.smc')}

    for ftype, ftuple in files.items():
        print(ftype)
        filename = os.path.join(datadir, ftype, ftuple[1])
        stream = ftuple[0](filename)
        std_dict = stream[0].stats.standard
        for key in REQUIRED:
            print('\t%s' % key)
            assert key in std_dict
        print(ftype, std_dict['source_format'])


if __name__ == '__main__':
    test_smc()
