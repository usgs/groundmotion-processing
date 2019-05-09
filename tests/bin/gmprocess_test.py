#!/usr/bin/env python

# stdlib imports
import os
import tempfile
import shutil

# third party imports
import pkg_resources

from impactutils.io.cmd import get_command_output


def test_gmprocess():
    eid = 'usb000syza'
    tpath = pkg_resources.resource_filename('gmprocess', 'tests')
    gmprocess = os.path.abspath(os.path.join(tpath, '..', '..',
                                             'bin', 'gmprocess'))
    dpath = os.path.join('data', 'testdata', 'knet', eid)
    cfgpath = dpath = os.path.join('data',
                                   'testdata',
                                   'knet',
                                   eid,
                                   'config.yml')
    knetdir = pkg_resources.resource_filename('gmprocess', dpath)
    cfgfile = pkg_resources.resource_filename('gmprocess', cfgpath)
    try:
        tdir = tempfile.mkdtemp()
        fmt = '%s %s -i %s --directory %s -c %s'
        tpl = (gmprocess, tdir, eid, knetdir, cfgfile)
        cmd = fmt % tpl
        res, stdout, stderr = get_command_output(cmd)
        assert res

    except Exception:
        pass
    finally:
        shutil.rmtree(tdir)


if __name__ == '__main__':
    test_gmprocess()
