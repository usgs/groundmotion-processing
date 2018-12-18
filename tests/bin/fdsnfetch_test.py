#!/usr/bin/env python

import subprocess
import os
from gmprocess.io.fdsn import request_raw_waveforms


def get_command_output(cmd):
    """
    Method for calling external system command.

    Args:
        cmd: String command (e.g., 'ls -l', etc.).

    Returns:
        Three-element tuple containing a boolean indicating success or failure,
        the stdout from running the command, and stderr.
    """
    proc = subprocess.Popen(cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                            )

    stdout, stderr = proc.communicate()
    retcode = proc.returncode
    if retcode == 0:
        retcode = True
    else:
        retcode = False
    return (retcode, stdout, stderr)


def test_fdsnfetch():
    homedir = os.path.dirname(os.path.abspath(__file__))
    fdsnfetch = os.path.join(homedir, '..', '..', 'bin', 'fdsnfetch')
    datadir = os.path.join(homedir, '..', 'data', 'fdsnfetch')

    parameters = 'IRIS 2001-02-28T18:54:32 47.149 -122.7266667 -dmax 1.0'
    parameters += ' -n UW -s ALCT -c EN* -r'
    cmd_input = '%s %s' % (datadir, parameters)
    cmd = '%s %s' % (fdsnfetch, cmd_input)
    res, stdout, stderr = get_command_output(cmd)
    print(stdout.decode('utf-8').strip())
    print(stderr.decode('utf-8').strip())

    # Confirm that we got the three ALCT files as expected
    st, inv = request_raw_waveforms('IRIS', '2001-02-28T18:54:32', 47.149,
                                    -122.7266667, before_time=120,
                                    after_time=120, dist_max=1.0,
                                    stations=['ALCT'], channels=['EN*'])
    assert len(st) == 3


if __name__ == '__main__':
    test_fdsnfetch()
