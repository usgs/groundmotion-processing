#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import shutil
import pkg_resources

from gmprocess.utils import constants


def test_export_shakemap(script_runner):
    try:
        # Need to create profile first.
        cdir = constants.PROJECTS_PATH_TEST
        ddir = pkg_resources.resource_filename(
            'gmprocess', os.path.join('data', 'testdata',
                                      'demo_steps', 'exports'))
        setup_inputs = io.StringIO(
            "2\ntest\n%s\n%s\nname\ntest@email.com\n" % (cdir, ddir)
        )
        ret = script_runner.run(
            'gmrecords', 'projects', '-c', stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run('gmrecords', 'shakemap')
        assert ret.success

        # Check that output files are created
        events = ['ci38457511', 'ci38038071']
        out_names = ['%s_metrics.json', '%s_groundmotions_dat.json']
        for event in events:
            for outname in out_names:
                dfile = os.path.join(ddir, event, outname % event)
                assert os.path.isfile(dfile)

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.PROJECTS_PATH_TEST)
        # Remove created files
        events = ['ci38457511', 'ci38038071']
        out_names = ['%s_metrics.json', '%s_groundmotions_dat.json']
        for event in events:
            for outname in out_names:
                dfile = os.path.join(ddir, event, outname % event)
                os.remove(dfile)


if __name__ == '__main__':
    test_export_shakemap()
