#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import shutil
import pkg_resources

from gmprocess.utils import constants


def test_export_provenance_tables(script_runner):
    try:
        # Need to create profile first.
        cdir = constants.PROJECTS_PATH_TEST
        ddir = pkg_resources.resource_filename(
            'gmprocess', os.path.join('data', 'testdata',
                                      'demo_steps', 'exports'))
        setup_inputs = io.StringIO(
            "2\ntest\n%s\n%s\nname\ntest@email.com\n" % (cdir, ddir)
        )
        ret = script_runner.run('gmrecords', 'projects', '-c',
                                stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run('gmrecords', 'ptables')
        assert ret.success

        # Check that files were created
        count = 0
        pattern = '_provenance'
        for root, _, files in os.walk(ddir):
            for file in files:
                if pattern in file:
                    count += 1
        assert count == 2

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.PROJECTS_PATH_TEST)
        # Remove created files
        pattern = '_provenance'
        for root, _, files in os.walk(ddir):
            for file in files:
                if pattern in file:
                    os.remove(os.path.join(root, file))


if __name__ == '__main__':
    test_export_provenance_tables()
