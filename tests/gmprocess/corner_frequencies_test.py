
import os

import numpy as np

from gmprocess.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.io.test_utils import read_data_dir
from gmprocess.config import get_config

from gmprocess.windows import signal_split
from gmprocess.windows import signal_end
from gmprocess.windows import window_checks

from gmprocess.processing import get_corner_frequencies
from gmprocess.processing import snr_check


def test_corner_frequencies():
    # Default config has 'constant' corner freuqnecy method, so the need
    # here is to force the 'snr' method.
    data_files, origin = read_data_dir('geonet', 'us1000778i', '*.V1A')
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    config = get_config()

    window_conf = config['windows']

    processed_streams = sc.copy()
    for st in processed_streams:
        if st.passed:
            # Estimate noise/signal split time
            split_conf = window_conf['split']
            event_time = origin['time']
            event_lon = origin['lon']
            event_lat = origin['lat']
            st = signal_split(
                st,
                event_time=event_time,
                event_lon=event_lon,
                event_lat=event_lat,
                **split_conf)

            # Estimate end of signal
            end_conf = window_conf['signal_end']
            event_mag = origin['magnitude']
            print(st)
            st = signal_end(
                st,
                event_time=event_time,
                event_lon=event_lon,
                event_lat=event_lat,
                event_mag=event_mag,
                **end_conf
            )
            wcheck_conf = window_conf['window_checks']
            st = window_checks(
                st,
                min_noise_duration=wcheck_conf['min_noise_duration'],
                min_signal_duration=wcheck_conf['min_signal_duration']
            )

    pconfig = config['processing']

    # Run SNR check
    test = [
        d for d in pconfig if list(d.keys())[0] == 'snr_check'
    ]
    snr_config = test[0]['snr_check']
    for stream in processed_streams:
        stream = snr_check(
            stream,
            **snr_config
        )

    # Run get_corner_frequencies
    test = [
        d for d in pconfig if list(d.keys())[0] == 'get_corner_frequencies'
    ]
    cf_config = test[0]['get_corner_frequencies']
    snr_config = cf_config['snr']

    lp = []
    hp = []
    for stream in processed_streams:
        stream = get_corner_frequencies(
            stream,
            method="snr",
            snr=snr_config
        )
        if stream[0].hasParameter('corner_frequencies'):
            cfdict = stream[0].getParameter('corner_frequencies')
            lp.append(cfdict['lowpass'])
            hp.append(cfdict['highpass'])
    np.testing.assert_allclose(
        np.sort(hp),
        np.array([0.0070111, 0.04400637]),
        atol=1e-6
    )


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_corner_frequencies()
