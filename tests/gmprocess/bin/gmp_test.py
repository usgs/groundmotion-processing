#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import shutil

from gmprocess.utils import constants


def test_gmp(script_runner):
    try:
        # Need to create profile first.
        setup_inputs = io.StringIO("test\n\n\nname\nemail\n")
        ret = script_runner.run('gmp', 'projects', '-c', stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run('gmp', '--version')
        assert ret.success

        ret = script_runner.run('gmp', '--help')
        assert ret.success
    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.PROJECTS_PATH_TEST)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_gmp()
