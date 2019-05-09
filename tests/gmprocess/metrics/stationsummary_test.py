#!/usr/bin/env python

# stdlib imports
import os.path
import warnings

# third party imports
import numpy as np
from obspy.core.event import Origin

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.io.test_utils import read_data_dir


def cmp_dicts(adict, bdict):
    for pgm, channels in adict.items():
        for channel, avalue in channels.items():
            bvalue = bdict[pgm][channel]
            print('Comparing %s->%s...' % (pgm, channel))
            np.testing.assert_almost_equal(avalue, bvalue)


def test_stationsummary():
    datafiles, _ = read_data_dir(
        'geonet', 'us1000778i', '20161113_110259_WTMC_20.V2A')
    datafile = datafiles[0]
    origin = Origin(latitude=42.6925, longitude=173.021944)

    target_imcs = np.sort(np.asarray(['GREATER_OF_TWO_HORIZONTALS',
                                      'HN1', 'HN2', 'HNZ', 'ROTD(50.0)',
                                      'ROTD(100.0)']))
    target_imts = np.sort(np.asarray(['SA(1.0)', 'PGA', 'PGV']))
    stream = read_geonet(datafile)[0]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stream_summary = StationSummary.from_stream(
            stream,
            ['greater_of_two_horizontals',
             'channels',
             'rotd50',
             'rotd100',
             'invalid'],
            ['sa1.0', 'PGA', 'pgv', 'invalid'], origin)
        original_stream = stream_summary.stream
        stream_summary.stream = []
        final_stream = stream_summary.stream
        assert original_stream == final_stream
        original_code = stream_summary.station_code
        np.testing.assert_array_equal(np.sort(stream_summary.components),
                                      target_imcs)
        np.testing.assert_array_equal(np.sort(stream_summary.imts),
                                      target_imts)
        np.testing.assert_almost_equal(stream_summary.get_pgm('PGA', 'HN1'),
                                       99.3173469387755, decimal=1)
        target_available = np.sort(np.asarray([
            'greater_of_two_horizontals', 'geometric_mean', 'arithmetic_mean',
            'channels', 'gmrotd', 'rotd', 'quadratic_mean',
            'radial_transverse']))
        imcs = stream_summary.available_imcs
        np.testing.assert_array_equal(np.sort(imcs), target_available)
        target_available = np.sort(np.asarray(['pga',
                                               'pgv',
                                               'sa',
                                               'arias',
                                               'fas']))
        imts = stream_summary.available_imts
        np.testing.assert_array_equal(np.sort(imts), target_available)
    test_pgms = {
        'PGV': {
            'ROTD(100.0)': 114.24894584734818,
            'ROTD(50.0)': 81.55436750525355,
            'HNZ': 37.47740000000001,
            'HN1': 100.81460000000004,
            'HN2': 68.4354,
            'GREATER_OF_TWO_HORIZONTALS': 100.81460000000004},
        'PGA': {
            'ROTD(100.0)': 100.73875535385548,
            'ROTD(50.0)': 91.40178541935455,
            'HNZ': 183.7722361866693,
            'HN1': 99.24999872535474,
            'HN2': 81.23467239067368,
            'GREATER_OF_TWO_HORIZONTALS': 99.24999872535474},
        'SA(1.0)': {
            'ROTD(100.0)': 146.9023350124098,
            'ROTD(50.0)': 106.03202302692158,
            'HNZ': 27.74118995438756,
            'HN1': 136.25041187387063,
            'HN2': 84.69296738413021,
            'GREATER_OF_TWO_HORIZONTALS': 136.25041187387063}
    }
    pgms = stream_summary.pgms
    for imt_str in test_pgms:
        for imc_str in test_pgms[imt_str]:
            imt = pgms.loc[pgms['IMT'] == imt_str]
            imc = imt.loc[imt['IMC'] == imc_str]
            results = imc.Result.tolist()
            assert len(results) == 1
            np.testing.assert_almost_equal(results[0], test_pgms[imt_str][imc_str],
                    decimal=10)

    # Test with fas
    stream = read_geonet(datafile)[0]
    stream_summary = StationSummary.from_stream(
        stream,
        ['greater_of_two_horizontals',
         'channels',
         'geometric_mean'],
        ['sa1.0', 'PGA', 'pgv', 'fas2.0'])
    target_imcs = np.sort(np.asarray(['GREATER_OF_TWO_HORIZONTALS',
                                      'HN1', 'HN2', 'HNZ',
                                      'GEOMETRIC_MEAN']))
    target_imts = np.sort(np.asarray(['SA(1.0)',
                                      'PGA', 'PGV', 'FAS(2.0)']))
    np.testing.assert_array_equal(np.sort(stream_summary.components),
                                  target_imcs)
    np.testing.assert_array_equal(np.sort(stream_summary.imts),
                                  target_imts)

    # Test config use
    stream = read_geonet(datafile)[0]
    stream_summary = StationSummary.from_config(stream)
    target_imcs = np.sort(np.asarray(['GREATER_OF_TWO_HORIZONTALS',
                                      'HN1', 'HN2', 'HNZ']))
    target_imts = np.sort(np.asarray(['SA(1.0)', 'SA(2.0)', 'SA(3.0)',
                                      'SA(0.3)', 'PGA', 'PGV', 'FAS(1.0)', 'FAS(2.0)',
                                      'FAS(3.0)', 'FAS(0.3)']))
    assert(stream_summary.smoothing == 'konno_ohmachi')
    assert(stream_summary.bandwidth == 20.0)
    assert(stream_summary.damping == 0.05)

    # test XML output
    stream = read_geonet(datafile)[0]
    imclist = ['greater_of_two_horizontals',
               'channels',
               'rotd50.0',
               'rotd100.0']
    imtlist = ['sa1.0', 'PGA', 'pgv', 'fas2.0', 'arias']
    stream_summary = StationSummary.from_stream(stream, imclist, imtlist)
    xmlstr = stream_summary.getMetricXML()
    print(xmlstr.decode('utf-8'))

    stream2 = StationSummary.fromMetricXML(xmlstr)
    cmp1 = np.sort(['GREATER_OF_TWO_HORIZONTALS', 'HN1', 'HN2', 'HNZ',
            'ROTD100.0', 'ROTD50.0'])
    cmp2 = np.sort(stream2.components)
    np.testing.assert_array_equal(cmp1, cmp2)
    imt1 = np.sort(stream_summary.imts)
    imt2 = np.sort(stream2.imts)
    np.testing.assert_array_equal(imt1, imt2)


if __name__ == '__main__':
    test_stationsummary()
