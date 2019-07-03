#!/usr/bin/env python

# stdlib imports
import os
import tempfile
import shutil
import glob

# third party imports
import pkg_resources
import pandas as pd
import numpy as np

from impactutils.io.cmd import get_command_output


def test_gmprocess():
    eid = 'usb000syza'
    tpath = pkg_resources.resource_filename('gmprocess', 'tests')
    gmprocess = os.path.abspath(os.path.join(tpath, '..', '..',
                                             'bin', 'gmprocess'))
    dpath = os.path.join('data', 'testdata', 'knet', eid)
    cfgpath = os.path.join('data',
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

    # Testing some colocated and strong motion broadband data and making
    # sure we get approximately the same PGA values in the final csv files
    test_folder = os.path.join(pkg_resources.resource_filename(
        'gmprocess', os.path.join('data', 'testdata', 'fdsn', 'uw61251926')))
    config = os.path.join(test_folder, '..', 'test_config.yml')
    pga_vals = []
    for ddir in glob.glob(os.path.join(test_folder, '*')):
        tdir = tempfile.mkdtemp()
        fmt = '%s -o %s --assemble --directory %s --process --export'
        fmt += ' --config %s'
        tpl = (gmprocess, tdir, ddir, config)
        cmd = fmt % tpl
        res, stdout, stderr = get_command_output(cmd)
        assert res
        pga = float(pd.read_csv(os.path.join(tdir, 'rotd50.0.csv'))['PGA'])
        pga_vals.append(pga)
        shutil.rmtree(tdir)
    assert np.allclose(pga_vals[0], pga_vals[1], atol=0.01)


if __name__ == '__main__':
    test_gmprocess()
