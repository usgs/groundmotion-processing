#!/usr/bin/env python

# stdlib imports
import os.path
import pkg_resources
import warnings

# third party imports
import numpy as np
from obspy.core.event import Origin
import pandas as pd

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.io.test_utils import read_data_dir
from gmprocess.metrics.exception import PGMException
from gmprocess.metrics.metrics_controller import MetricsController
from gmprocess.stationstream import StationStream


def test_controller():
    datafiles, event = read_data_dir(
        'geonet', 'us1000778i', '20161113_110259_WTMC_20.V2A')
    datafile = datafiles[0]
    input_imts = ['pgv', 'pga', 'sa2', 'sa1.0', 'sa0.3',
                  'fas2', 'fas1.0', 'fas0.3', 'arias', 'invalid']
    input_imcs = ['rotd50', 'rotd100.0', 'gmrotd50', 'gmrotd100.0',
                  'radial_transverse', 'geometric_mean', 'arithmetic_mean', 'channels',
                  'greater_of_two_horizontals', 'invalid', 'quadratic_mean']
    stream_v2 = read_geonet(datafile)[0]

    # Testing for acceleration --------------------------
    m1 = MetricsController(input_imts, input_imcs, stream_v2, event=event)
    pgms = m1.pgms

    # testing for pga, pgv, sa
    target_imcs = ['ROTD(50.0)', 'ROTD(100.0)', 'GMROTD(50.0)',
                   'GMROTD(100.0)', 'HNR', 'HNT', 'GEOMETRIC_MEAN', 'ARITHMETIC_MEAN', 'H1', 'H2',
                   'Z', 'GREATER_OF_TWO_HORIZONTALS', 'QUADRATIC_MEAN']
    for col in ['PGA', 'PGV', 'SA(1.0)', 'SA(2.0)', 'SA(0.3)']:
        imt = pgms.loc[pgms['IMT'] == col]
        imcs = imt['IMC'].tolist()
        assert len(imcs) == len(target_imcs)
        np.testing.assert_array_equal(np.sort(imcs), np.sort(target_imcs))

    # testing for fas
    for col in ['FAS(1.0)', 'FAS(2.0)', 'FAS(0.3)']:
        imt = pgms.loc[pgms['IMT'] == col]
        imcs = imt['IMC'].tolist()
        assert len(imcs) == 3
        np.testing.assert_array_equal(np.sort(imcs), ['ARITHMETIC_MEAN',
                                                      'GEOMETRIC_MEAN', 'QUADRATIC_MEAN'])

    # testing for arias
    imt = pgms.loc[pgms['IMT'] == 'ARIAS']
    imcs = imt['IMC'].tolist()
    assert len(imcs) == 1
    np.testing.assert_array_equal(np.sort(imcs), ['ARITHMETIC_MEAN'])
    _validate_steps(m1.step_sets, 'acc')

    # Testing for Velocity --------------------------
    for trace in stream_v2:
        trace.stats.standard.units = 'vel'
    m = MetricsController(input_imts, input_imcs, stream_v2, event=event)
    pgms = m.pgms

    # testing for pga, pgv, sa
    target_imcs = ['ROTD(50.0)', 'ROTD(100.0)', 'GMROTD(50.0)',
                   'GMROTD(100.0)', 'HNR', 'HNT', 'GEOMETRIC_MEAN', 'ARITHMETIC_MEAN',
                   'QUADRATIC_MEAN', 'H1', 'H2',
                   'Z', 'GREATER_OF_TWO_HORIZONTALS']
    for col in ['PGA', 'PGV', 'SA(1.0)', 'SA(2.0)', 'SA(0.3)']:
        imt = pgms.loc[pgms['IMT'] == col]
        imcs = imt['IMC'].tolist()
        assert len(imcs) == len(target_imcs)
        np.testing.assert_array_equal(np.sort(imcs), np.sort(target_imcs))

    # testing for fas
    for col in ['FAS(1.0)', 'FAS(2.0)', 'FAS(0.3)']:
        imt = pgms.loc[pgms['IMT'] == col]
        imcs = imt['IMC'].tolist()
        assert len(imcs) == 3
        np.testing.assert_array_equal(np.sort(imcs), ['ARITHMETIC_MEAN',
                                                      'GEOMETRIC_MEAN', 'QUADRATIC_MEAN'])

    # testing for arias
    imt = pgms.loc[pgms['IMT'] == 'ARIAS']
    imcs = imt['IMC'].tolist()
    assert len(imcs) == 1
    np.testing.assert_array_equal(np.sort(imcs), ['ARITHMETIC_MEAN'])
    _validate_steps(m.step_sets, 'vel')


def _validate_steps(step_sets, data_type):
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    pathfile = datafile_v2 = os.path.join(homedir, '..', '..', 'data',
                                          'metrics_controller', 'workflows.csv')
    df = pd.read_csv(pathfile)
    wf_df = df.apply(lambda x: x.astype(str).str.lower())
    # test workflows
    for step_set in step_sets:
        steps = step_sets[step_set]
        imt = steps['imt']
        imc = steps['imc']
        row = wf_df[(wf_df.IMT == imt) & (wf_df.IMC == imc)
                    & (wf_df.Data == data_type)]
        assert steps['Transform1'] == row['Transform1'].iloc[0]
        assert steps['Transform2'] == row['Transform2'].iloc[0]
        assert steps['Transform3'] == row['Transform3'].iloc[0]
        assert steps['Combination1'] == row['Combination1'].iloc[0]
        assert steps['Combination2'] == row['Combination2'].iloc[0]
        assert steps['Rotation'] == row['Rotation'].iloc[0]
        assert steps['Reduction'] == row['Reduction'].iloc[0]


def test_exceptions():
    ddir = os.path.join('data', 'testdata', 'geonet')
    homedir = pkg_resources.resource_filename('gmprocess', ddir)
    datafile_v2 = os.path.join(
        homedir, 'us1000778i', '20161113_110259_WTMC_20.V2A')
    stream_v2 = read_geonet(datafile_v2)[0]
    # Check for origin Error
    passed = True
    try:
        m = MetricsController('pga', 'radial_transverse', stream_v2)
    except PGMException as e:
        passed = False
    assert passed == False

    # -------- Horizontal Channel Errors -----------
    # Check for horizontal passthrough gm
    st2 = stream_v2.select(component='[N1]')
    st3 = stream_v2.select(component='Z')
    st1 = StationStream([st2[0], st3[0]])
    passed = True
    m = MetricsController('pga', 'geometric_mean', st1)
    pgm = m.pgms
    result = pgm['Result'].tolist()[0]
    assert np.isnan(result)
    # Check for horizontal passthrough rotd50
    m = MetricsController('pga', 'rotd50', st1)
    pgm = m.pgms
    result = pgm['Result'].tolist()[0]
    assert np.isnan(result)
    # Check for horizontal passthrough gmrotd50
    m = MetricsController('pga', 'gmrotd50', st1)
    pgm = m.pgms
    result = pgm['Result'].tolist()[0]
    assert np.isnan(result)
    # No horizontal channels
    try:
        m = MetricsController('sa3.0', 'channels', st3)
    except PGMException as e:
        passed = False
    assert passed == False


def test_end_to_end():
    datafiles, _ = read_data_dir(
        'geonet', 'us1000778i', '20161113_110259_WTMC_20.V2A')
    datafile = datafiles[0]

    target_imcs = np.sort(np.asarray(['GREATER_OF_TWO_HORIZONTALS',
                                      'H1', 'H2', 'Z', 'ROTD50.0',
                                      'ROTD100.0']))
    target_imts = np.sort(np.asarray(['SA(1.0)', 'PGA', 'PGV']))
    stream = read_geonet(datafile)[0]
    input_imcs = ['greater_of_two_horizontals', 'channels', 'rotd50',
                  'rotd100', 'invalid']
    input_imts = ['sa1.0', 'PGA', 'pgv', 'invalid']
    m = MetricsController(input_imts, input_imcs, stream)
    test_pgms = [
        ('PGV', 'ROTD(100.0)', 114.24894584734818),
        ('PGV', 'ROTD(50.0)', 81.55436750525355),
        ('PGV', 'Z', 37.47740000000001),
        ('PGV', 'H1', 100.81460000000004),
        ('PGV', 'H2', 68.4354),
        ('PGV', 'GREATER_OF_TWO_HORIZONTALS', 100.81460000000004),
        ('PGA', 'ROTD(100.0)', 100.73875535385548),
        ('PGA', 'ROTD(50.0)', 91.40178541935455),
        ('PGA', 'Z', 183.7722361866693),
        ('PGA', 'H1', 99.24999872535474),
        ('PGA', 'H2', 81.23467239067368),
        ('PGA', 'GREATER_OF_TWO_HORIZONTALS', 99.24999872535474),
        ('SA(1.0)', 'ROTD(100.0)', 146.9023350124098),
        ('SA(1.0)', 'ROTD(50.0)', 106.03202302692158),
        ('SA(1.0)', 'Z', 27.74118995438756),
        ('SA(1.0)', 'H1', 136.25041187387063),
        ('SA(1.0)', 'H2', 84.69296738413021),
        ('SA(1.0)', 'GREATER_OF_TWO_HORIZONTALS', 136.25041187387063)
    ]
    pgms = m.pgms
    assert len(pgms['IMT'].tolist()) == len(test_pgms)
    for target in test_pgms:
        target_imt = target[0]
        target_imc = target[1]
        value = target[2]
        sub_imt = pgms.loc[pgms['IMT'] == target_imt]
        df = sub_imt.loc[sub_imt['IMC'] == target_imc]
        assert len(df['IMT'].tolist()) == 1

        np.testing.assert_array_almost_equal(df['Result'].tolist()[0], value,
                                             decimal=10)


if __name__ == '__main__':
    test_controller()
    test_exceptions()
    test_end_to_end()
