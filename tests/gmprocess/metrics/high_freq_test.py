#!/usr/bin/env python

import os
import pkg_resources

import numpy as np
import csv

from obspy.core.trace import Stats

from gmprocess.stationstream import StationStream
from gmprocess.stationtrace import StationTrace
from gmprocess.metrics.station_summary import StationSummary


def read_at2(dfile, horient=0.0):
    # This is a conveneince method so we can read in these specific data for
    # testing, it is not a general purpose reader since this format does not
    # contain a lot of metadata that is generally required for it to be useful.
    skiprows = 4
    datafile = open(dfile, 'r')
    datareader = csv.reader(datafile)
    data = []
    header = []
    # for i in range(skiprows):
    # next(datareader)
    #    header.append(datareader.readlines())
    count = 0
    for row in datareader:
        if count < skiprows:
            header.append(row)
        else:
            data.extend([float(e) for e in row[0].split()])
        count += 1
    datafile.close()

    hdr = {}
    hdr['network'] = ''
    hdr['station'] = ''
    if horient == 0:
        hdr['channel'] = 'BH1'
    else:
        hdr['channel'] = 'BH2'
    hdr['location'] = '--'

    dt = float(header[3][1].split('=')[1].strip().lower().replace('sec', ''))
    hdr['npts'] = len(data)
    hdr['sampling_rate'] = 1 / dt
    hdr['duration'] = (hdr['npts'] - 1) / hdr['sampling_rate']

    hdr['starttime'] = 0

    # There is no lat/lon...
    hdr['coordinates'] = {
        'latitude': 0.0,
        'longitude': 0.0,
        'elevation': 0.0
    }

    standard = {}
    standard['units'] = 'acc'
    standard['units_type'] = 'acc'
    standard['horizontal_orientation'] = horient
    standard['vertical_orientation'] = np.nan
    standard['source_file'] = dfile
    standard['station_name'] = ''
    standard['corner_frequency'] = 30.0
    standard['structure_type'] = ''
    standard['comments'] = ''
    standard['instrument'] = ''
    standard['instrument_period'] = 1.0
    standard['instrument_sensitivity'] = 1.0
    standard['source'] = 'PEER'
    standard['instrument_damping'] = 0.1
    standard['sensor_serial_number'] = ''
    standard['process_level'] = 'corrected physical units'
    standard['source_format'] = 'AT2'
    standard['process_time'] = ''
    hdr['standard'] = standard
    # convert data from g to cm/s^2
    g_to_cmss = 980.665
    tr = StationTrace(np.array(data.copy()) * g_to_cmss, Stats(hdr.copy()))
    response = {'input_units': 'counts', 'output_units': 'cm/s^2'}
    tr.setProvenance('remove_response', response)
    return tr


def test_high_freq_sa():
    datapath = os.path.join('data', 'testdata', 'high_freq_sa')
    datadir = pkg_resources.resource_filename('gmprocess', datapath)
    # fnames = [
    #     'RSN10591_ComalTX11-10-20_IU.CCM.BH1.10.AT2',
    #     'RSN10591_ComalTX11-10-20_IU.CCM.BH2.10.AT2'
    # ]
    fnames = [
        'RSN10590_ComalTX11-10-20_IU.CCM.BH1.00.AT2',
        'RSN10590_ComalTX11-10-20_IU.CCM.BH2.00.AT2'
    ]
    dfile = os.path.join(datadir, fnames[0])
    h1 = read_at2(dfile)
    dfile = os.path.join(datadir, fnames[1])
    h2 = read_at2(dfile, horient=90.0)
    st = StationStream([h1, h2])

    periods = [
        0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.3,
        0.4, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 7.5, 10.0
    ]
    imt_list = ['sa%s' % p for p in periods]
    station = StationSummary.from_stream(st, ['rotd50'], imt_list)
    # I believe that units are %g in the following table:
    pgmdf = station.pgms
    imt_strs = ['SA(%.3f)' % p for p in periods]
    test_sa = []
    for i in imt_strs:
        test_sa.append(pgmdf.loc[i, 'ROTD(50.0)'].Result)

    # Target (from PEER NGA East Flatfile)
    test_data = {
        'periods': periods,
        'target_sa': [
            0.00000265693, 0.00000265828, 0.00000263894, 0.00000265161,
            0.00000260955, 0.0000026616, 0.00000276549, 0.00000308482,
            0.00000380387, 0.00000391716,  # 0.3
            0.00000576159, 0.00000772915, 0.00000817996, 0.00000768231,  # 1.0
            0.00000492174, 0.00000556708, 0.00000213793, 0.00000126181,
            0.00000127302, 0.000000430723, 0.000000277972
        ],
        'test_sa': np.array(test_sa) / 100
    }

    # For visualization... not testing:
    if False:
        import matplotlib.pyplot as plt
        # %matplotlib osx

        plt.loglog(test_data['periods'],
                   test_data['target_sa'],
                   'o-', label='PEER')
        plt.loglog(test_data['periods'],
                   test_data['test_sa'],
                   'o-', label='gmprocess')
        plt.xlabel('Period, sec')
        plt.ylabel('PSA, g')
        plt.legend()


if __name__ == '__main__':
    test_high_freq_sa()
