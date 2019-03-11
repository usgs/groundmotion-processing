#!/usr/bin/env python

import os
from gmprocess.io.fdsn import request_raw_waveforms
from impactutils.io.cmd import get_command_output


def test_fdsnfetch():
    # homedir = os.path.dirname(os.path.abspath(__file__))
    # fdsnfetch = os.path.join(homedir, '..', '..', 'bin', 'fdsnfetch')
    # datadir = os.path.join(homedir, '..', 'data', 'fdsnfetch')

    # parameters = '2001-02-28T18:54:32 47.149 -122.7266667 '
    # cmd_input = '%s %s' % (datadir, parameters)
    # cmd = '%s %s' % (fdsnfetch, cmd_input)
    # res, stdout, stderr = get_command_output(cmd)
    # print(stdout.decode('utf-8').strip())
    # print(stderr.decode('utf-8').strip())

    # Confirm that we got the three ALCT files as expected
    st, inv = request_raw_waveforms(
        'IRIS', '2001-02-28T18:54:32', 47.149,
        -122.7266667, before_time=120,
        after_time=120, dist_max=1.0,
        stations=['ALCT'], networks=["UW"],
        channels=['EN*'])
    assert len(st) == 3


if __name__ == '__main__':
    test_fdsnfetch()
