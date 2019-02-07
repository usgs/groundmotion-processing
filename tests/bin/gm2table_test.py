#!/usr/bin/env python

# stdlib imports
import os
import subprocess
import tempfile

# third party imports
from lxml import etree


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


def test_gm2table():
    homedir = os.path.dirname(os.path.abspath(__file__))
    gm2table = os.path.join(homedir, '..', '..', 'bin', 'gm2table')
    knetdir = os.path.join(homedir, '..', 'data', 'knet')

    tfile = tempfile.mkstemp()[1]
    cmd = '%s %s -f csv' % (gm2table, knetdir)
    res, stdout, stderr = get_command_output(cmd)
    os.remove(tfile)

    tfile = tempfile.mkstemp()[1]
    cmd = '%s %s -f xlsx' % (gm2table, knetdir)
    res, stdout, stderr = get_command_output(cmd)
    os.remove(tfile)

if __name__ == '__main__':
    test_gm2table()
