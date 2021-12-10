#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import os.path
import pkg_resources

# third party imports
import numpy as np
import pandas as pd

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.metrics.exception import PGMException
from gmprocess.metrics.metrics_controller import \
    MetricsController, _get_channel_dict
from gmprocess.core.stationstream import StationStream
from gmprocess.utils.config import get_config

config = get_config()


def test_get_channel_dict():
    channel_names1 = ['HNN', 'HNE', 'HNZ']
    cdict, _ = _get_channel_dict(channel_names1)
    assert sorted(cdict.keys()) == ['H1', 'H2', 'Z']

    channel_names2 = ['HN1', 'HN2', 'HNZ']
    cdict, _ = _get_channel_dict(channel_names2)
    assert sorted(cdict.keys()) == ['H1', 'H2', 'Z']

    channel_names3 = ['HN1', 'HNE', 'HNZ']
    cdict, _ = _get_channel_dict(channel_names3)
    assert sorted(cdict.keys()) == ['H1', 'H2', 'Z']

    channel_names4 = ['HN1', 'HNZ']
    cdict, _ = _get_channel_dict(channel_names4)
    assert sorted(cdict.keys()) == ['H1', 'Z']

    channel_names5 = ['HN2', 'HN3', 'HNZ']
    cdict, _ = _get_channel_dict(channel_names5)
    assert sorted(cdict.keys()) == ['H1', 'H2', 'Z']

    channel_names6 = ['HN2', 'HN3']
    cdict, _ = _get_channel_dict(channel_names6)
    assert sorted(cdict.keys()) == ['H1', 'H2']

    channel_names7 = ['HN2', 'HNZ']
    cdict, _ = _get_channel_dict(channel_names7)
    assert sorted(cdict.keys()) == ['H1', 'Z']

    channel_names8 = ['HN2']
    cdict, _ = _get_channel_dict(channel_names8)
    assert sorted(cdict.keys()) == ['H1']

    channel_names9 = ['HN1']
    cdict, _ = _get_channel_dict(channel_names9)
    assert sorted(cdict.keys()) == ['H1']

    channel_names10 = ['HNZ']
    cdict, _ = _get_channel_dict(channel_names10)
    assert sorted(cdict.keys()) == ['Z']


def test_controller():
    datafiles, event = read_data_dir(
        'geonet', 'us1000778i', '20161113_110259_WTMC_20.V2A')
    datafile = datafiles[0]
    input_imts = ['pgv', 'pga', 'sa2', 'sa1.0', 'sa0.3',
                  'fas2', 'fas1.0', 'fas0.3', 'arias', 'invalid']
    input_imcs = ['rotd50', 'rotd100.0',
                  'radial_transverse', 'geometric_mean', 'arithmetic_mean',
                  'channels', 'greater_of_two_horizontals', 'invalid',
                  'quadratic_mean']
    stream_v2 = read_geonet(datafile)[0]

    # Testing for acceleration --------------------------
    m1 = MetricsController(input_imts, input_imcs, stream_v2, event=event,
                           config=config)
    pgms = m1.pgms

    # testing for pga, pgv, sa
    target_imcs = ['ROTD(50.0)', 'ROTD(100.0)', 'HNR', 'HNT', 'GEOMETRIC_MEAN',
                   'ARITHMETIC_MEAN', 'H1', 'H2', 'Z',
                   'GREATER_OF_TWO_HORIZONTALS', 'QUADRATIC_MEAN']
    for col in ['PGA', 'PGV', 'SA(1.000)', 'SA(2.000)', 'SA(0.300)']:
        imcs = pgms.loc[col].index.tolist()
        assert len(imcs) == len(target_imcs)
        np.testing.assert_array_equal(np.sort(imcs), np.sort(target_imcs))

    # testing for fas
    for col in ['FAS(1.000)', 'FAS(2.000)', 'FAS(0.300)']:
        imcs = pgms.loc[col].index.tolist()
        assert len(imcs) == 9
        np.testing.assert_array_equal(
            np.sort(imcs),
            ['ARITHMETIC_MEAN', 'GEOMETRIC_MEAN', 'GREATER_OF_TWO_HORIZONTALS',
             'H1', 'H2', 'HNR', 'HNT', 'QUADRATIC_MEAN', 'Z']
        )

    # testing for arias
    imcs = pgms.loc['ARIAS'].index.tolist()
    assert len(imcs) == 9
    np.testing.assert_array_equal(
        np.sort(imcs),
        ['ARITHMETIC_MEAN', 'GEOMETRIC_MEAN', 'GREATER_OF_TWO_HORIZONTALS',
         'H1', 'H2', 'HNR', 'HNT', 'QUADRATIC_MEAN', 'Z']
    )
    _validate_steps(m1.step_sets, 'acc')

    # Testing for Velocity --------------------------
    for trace in stream_v2:
        trace.stats.standard.units = 'vel'
    m = MetricsController(input_imts, input_imcs, stream_v2, event=event,
                          config=config)
    pgms = m.pgms

    # testing for pga, pgv, sa
    target_imcs = ['ROTD(50.0)', 'ROTD(100.0)', 'HNR', 'HNT', 'GEOMETRIC_MEAN',
                   'ARITHMETIC_MEAN', 'QUADRATIC_MEAN', 'H1', 'H2',
                   'Z', 'GREATER_OF_TWO_HORIZONTALS']
    for col in ['PGA', 'PGV', 'SA(1.000)', 'SA(2.000)', 'SA(0.300)']:
        imcs = pgms.loc[col].index.tolist()
        assert len(imcs) == len(target_imcs)
        np.testing.assert_array_equal(np.sort(imcs), np.sort(target_imcs))

    # testing for fas
    for col in ['FAS(1.000)', 'FAS(2.000)', 'FAS(0.300)']:
        imcs = pgms.loc[col].index.tolist()
        assert len(imcs) == 9
        np.testing.assert_array_equal(
            np.sort(imcs),
            ['ARITHMETIC_MEAN', 'GEOMETRIC_MEAN', 'GREATER_OF_TWO_HORIZONTALS',
             'H1', 'H2', 'HNR', 'HNT', 'QUADRATIC_MEAN', 'Z']
        )

    # testing for arias
    imcs = pgms.loc['ARIAS'].index.tolist()
    assert len(imcs) == 9
    np.testing.assert_array_equal(
        np.sort(imcs),
        ['ARITHMETIC_MEAN', 'GEOMETRIC_MEAN', 'GREATER_OF_TWO_HORIZONTALS',
         'H1', 'H2', 'HNR', 'HNT', 'QUADRATIC_MEAN', 'Z'
         ])
    _validate_steps(m.step_sets, 'vel')


def _validate_steps(step_sets, data_type):
    datafile = os.path.join(
        'data', 'testdata', 'metrics_controller', 'workflows.csv')
    datafile_abspath = pkg_resources.resource_filename('gmprocess', datafile)
    df = pd.read_csv(datafile_abspath)
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
        m = MetricsController('pga', 'radial_transverse', stream_v2,
                              config=config)
    except PGMException as e:
        passed = False
    assert passed == False

    # -------- Horizontal Channel Errors -----------
    # Check for horizontal passthrough gm
    st2 = stream_v2.select(component='[N1]')
    st3 = stream_v2.select(component='Z')
    st1 = StationStream([st2[0], st3[0]])
    passed = True
    m = MetricsController('pga', 'geometric_mean', st1, config=config)
    pgm = m.pgms
    result = pgm['Result'].tolist()[0]
    assert np.isnan(result)
    # Check for horizontal passthrough rotd50
    m = MetricsController('pga', 'rotd50', st1, config=config)
    pgm = m.pgms
    result = pgm['Result'].tolist()[0]
    assert np.isnan(result)
    # Check for horizontal passthrough gmrotd50
    m = MetricsController('pga', 'gmrotd50', st1, config=config)
    pgm = m.pgms
    result = pgm['Result'].tolist()[0]
    assert np.isnan(result)
    # No horizontal channels
    try:
        m = MetricsController('sa3.0', 'channels', st3, config=config)
    except PGMException as e:
        passed = False
    assert passed == False


def test_end_to_end():
    datafiles, _ = read_data_dir(
        'geonet', 'us1000778i', '20161113_110259_WTMC_20.V2A')
    datafile = datafiles[0]

    stream = read_geonet(datafile)[0]
    input_imcs = ['greater_of_two_horizontals', 'channels', 'rotd50',
                  'rotd100', 'invalid']
    input_imts = ['sa1.0', 'PGA', 'pgv', 'invalid']
    m = MetricsController(input_imts, input_imcs, stream, config=config)
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
        ('SA(1.000)', 'ROTD(100.0)', 146.9023350124098),
        ('SA(1.000)', 'ROTD(50.0)', 106.03202302692158),
        ('SA(1.000)', 'Z', 27.74118995438756),
        ('SA(1.000)', 'H1', 136.25041187387063),
        ('SA(1.000)', 'H2', 84.69296738413021),
        ('SA(1.000)', 'GREATER_OF_TWO_HORIZONTALS', 136.25041187387063)
    ]
    pgms = m.pgms
    assert len(pgms) == len(test_pgms)
    for target in test_pgms:
        target_imt = target[0]
        target_imc = target[1]
        value = target[2]
        df = pgms.loc[target_imt, target_imc]
        assert len(df) == 1

        np.testing.assert_array_almost_equal(
            df['Result'], value,
            decimal=10)


if __name__ == '__main__':
    test_get_channel_dict()
    test_controller()
    test_exceptions()
    test_end_to_end()
