import os
import pkg_resources

import numpy as np
from obspy import UTCDateTime

from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.config import get_config, update_dict
from gmprocess.utils.event import get_event_object
from gmprocess.waveform_processing.processing import process_streams


def test_zero_crossings():
    datapath = os.path.join('data', 'testdata', 'zero_crossings')
    datadir = pkg_resources.resource_filename('gmprocess', datapath)
    sc = StreamCollection.from_directory(datadir)
    sc.describe()

    conf = get_config()

    update = {
        'processing': [
            {'detrend': {'detrending_method': 'demean'}},
            {'check_zero_crossings': {'min_crossings': 1}}
        ]
    }
    update_dict(conf, update)

    edict = {
        'id': 'ak20419010',
        'time': UTCDateTime('2018-11-30T17:29:29'),
        'lat': 61.346,
        'lon': -149.955,
        'depth': 46.7,
        'magnitude': 7.1
    }
    event = get_event_object(edict)
    test = process_streams(sc, event, conf)
    for st in test:
        for tr in st:
            assert tr.hasParameter('ZeroCrossingRate')
    np.testing.assert_allclose(
        test[0][0].getParameter('ZeroCrossingRate')['crossing_rate'],
        0.008888888888888889,
        atol=1e-5)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_zero_crossings()
