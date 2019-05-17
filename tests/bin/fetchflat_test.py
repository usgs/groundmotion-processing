#!/usr/bin/env python

# stdlib imports
import os
import tempfile
import shutil

# third party imports
import pkg_resources

from impactutils.io.cmd import get_command_output


def test_fetchflat():
    tpath = pkg_resources.resource_filename('gmprocess', 'tests')
    fetchflat = os.path.abspath(os.path.join(tpath, '..', '..',
                                             'bin', 'fetchflat'))
    dpath = os.path.join('data', 'testdata', 'geonet2')
    cfgpath = os.path.join('data',
                           'testdata',
                           'geonet2',
                           'config.yml')
    datadir = pkg_resources.resource_filename('gmprocess', dpath)
    cfgfile = pkg_resources.resource_filename('gmprocess', cfgpath)
    try:
        tdir = tempfile.mkdtemp()
        fmt = '%s %s --directory %s -c %s'
        tpl = (fetchflat, tdir, datadir, cfgfile)
        cmd = fmt % tpl
        res, stdout, stderr = get_command_output(cmd)
        assert res

    except Exception:
        pass
    finally:
        shutil.rmtree(tdir)


if __name__ == '__main__':
    test_fetchflat()
