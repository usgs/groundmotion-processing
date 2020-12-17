#!/usr/bin/env python3

import os
import math
import pandas as pd

from gmprocess.utils.tables import set_precisions


def test_set_precisions():
    # Create an arbitrary dataframe for testing
    cols = ['EarthquakeLatitude', 'EarthquakeLongitude', 'EarthquakeDepth',
            'EarthquakeMagnitude', 'StationElevation', 'SamplingRate',
            'StationLatitude', 'StationLongitude', 'EpicentralDistance',
            'RuptureDistance', 'PGA', 'PGV', 'SA(1.0)', 'FAS(0.25)', 'ARIAS',
            'DURATION']
    df = pd.DataFrame.from_dict({'row1': [math.pi] * len(cols)},
                                orient='index', columns=cols)
    df = set_precisions(df)
    row1 = df.iloc[0]

    assert row1['EarthquakeLatitude'] == '3.14159'
    assert row1['EarthquakeLongitude'] == '3.14159'
    assert row1['EarthquakeMagnitude'] == '3.1'
    assert row1['StationLatitude'] == '3.14159'
    assert row1['StationLongitude'] == '3.14159'
    assert row1['StationElevation'] == '3.14'
    assert row1['SamplingRate'] == '3'
    assert row1['EarthquakeDepth'] == '3.14'
    assert row1['EpicentralDistance'] == '3.14'
    assert row1['RuptureDistance'] == '3.14'


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_set_precisions()
