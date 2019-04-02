#!/usr/bin/env python

# stdlib imports
import os
import tempfile

# third party imports
import pkg_resources

from impactutils.io.cmd import get_command_output


def test_gm2table():
    tpath = pkg_resources.resource_filename('gmprocess', 'tests')
    gm2table = os.path.abspath(os.path.join(tpath, '..', '..',
                                            'bin', 'gm2table'))
    dpath = os.path.join('data', 'testdata', 'knet')
    knetdir = pkg_resources.resource_filename('gmprocess', dpath)

    tfile = tempfile.mkstemp()[1]
    cmd = '%s %s %s -f csv' % (gm2table, knetdir, tfile)
    res, stdout, stderr = get_command_output(cmd)
    os.remove(tfile)

    tfile = tempfile.mkstemp()[1]
    cmd = '%s %s %s -f xlsx' % (gm2table, knetdir, tfile)
    res, stdout, stderr = get_command_output(cmd)
    os.remove(tfile)

    cwbdir = os.path.join(knetdir, '..', 'cwb')
    lon = 21.69
    lat = 24.14
    tfile = tempfile.mkstemp()[1]
    cmd = '%s %s %s --lat %s --lon %s' % (gm2table, cwbdir, tfile, lat, lon)
    res, stdout, stderr = get_command_output(cmd)
    os.remove(tfile)


if __name__ == '__main__':
    test_gm2table()
