#!/usr/bin/env python

# stdlib imports
import os
import subprocess
import tempfile

# third party imports
from lxml import etree

from impactutils.io.cmd import get_command_output


def test_gm2table():
    homedir = os.path.dirname(os.path.abspath(__file__))
    gm2table = os.path.join(homedir, '..', '..', 'bin', 'gm2table')
    knetdir = os.path.join(homedir, '..', 'data', 'knet')

    tfile = tempfile.mkstemp()[1]
    cmd = '%s %s %s -f csv' % (gm2table, knetdir, tfile)
    res, stdout, stderr = get_command_output(cmd)
    os.remove(tfile)

    tfile = tempfile.mkstemp()[1]
    cmd = '%s %s %s -f xlsx' % (gm2table, knetdir, tfile)
    res, stdout, stderr = get_command_output(cmd)
    os.remove(tfile)


    knetdir = os.path.join(homedir, '..', 'data', 'cwb')
    lon = 21.69
    lat = 24.14
    tfile = tempfile.mkstemp()[1]
    cmd = '%s %s %s --lat %s --lon %s' % (gm2table, knetdir, tfile, lat, lon)
    res, stdout, stderr = get_command_output(cmd)
    os.remove(tfile)

if __name__ == '__main__':
    test_gm2table()
