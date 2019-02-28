#!/usr/bin/env python

# stdlib imports
import os.path

# third party imports
import numpy as np
from obspy.core.stream import Stream
from obspy.core.trace import Trace

# local imports
from gmprocess.metrics.imt.fas import calculate_fas


def test_fas():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    fas_file = os.path.join(homedir, '..', '..', 'data', 'fas_results')
    p1 = os.path.join(homedir, '..', '..', 'peer', 'RSN763_LOMAP_GIL067.AT2')
    p2 = os.path.join(homedir, '..', '..', 'peer', 'RSN763_LOMAP_GIL337.AT2')

    stream = Stream()
    for idx, fpath in enumerate([p1, p2]):
        with open(fpath) as file_obj:
            for _ in range(3):
                next(file_obj)
            meta = re.findall(r'[.0-9]+', next(file_obj))
            count = int(meta[0])
            dt = float(meta[1])
            accels = np.array(
                    [col for line in file_obj for col in line.split()])
        trace = Trace(data=accels, header={
                'channel': 'H' + str(idx),
                'sampling_rate': 1/dt,
                'units': '%g'})
        stream.append(trace)

    freqs, fas = np.loadtxt(fas_file, unpack=True, usecols=(0,1))
    fas_dict = calculate_fas(stream, '', 1 / freqs, 'konno_ohmachi', 30)



if __name__ == '__main__':
    test_fas()
