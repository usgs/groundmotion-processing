#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import shutil
import pkg_resources

from gmprocess.utils import constants


def test_assemble(script_runner):
    try:
        # Need to create profile first.
        cdir = constants.PROJECTS_PATH_TEST
        ddir = pkg_resources.resource_filename(
            'gmprocess', os.path.join('data', 'testdata', 'demo'))
        setup_inputs = io.StringIO(
            "2\ntest\n%s\n%s\nname\nemail\n" % (cdir, ddir)
        )
        ret = script_runner.run(
            'gmrecords', 'projects', '-c', stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run('gmrecords', 'assemble', '-h')
        assert ret.success

        ret = script_runner.run('gmrecords', 'assemble')
        assert ret.success

        ret = script_runner.run(
            'gmrecords', 'assemble', '-e', 'ci38457511', '-o')
        assert ret.success

        external_source = pkg_resources.resource_filename(
            'gmprocess', os.path.join('data', 'testdata', 'demo2'))
        ret = script_runner.run(
            'gmrecords', 'assemble', '-e', 'usp000a1b0', '-d', external_source)
        assert ret.success

        # Check that output files are created
        events = ['ci38457511', 'ci38038071', 'usp000a1b0']
        out_names = ['workspace.h5']
        for event in events:
            for outname in out_names:
                dfile = os.path.join(ddir, event, outname)
                print(dfile)
                assert os.path.isfile(dfile)

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.PROJECTS_PATH_TEST)
        # Remove workspace and image files
        pattern = ['workspace.h5', '.png']
        for root, _, files in os.walk(ddir):
            for file in files:
                if any(file.endswith(ext) for ext in pattern):
                    os.remove(os.path.join(root, file))
        rmdir = os.path.join(ddir, 'usp000a1b0')
        shutil.rmtree(rmdir)


if __name__ == '__main__':
    test_assemble()
