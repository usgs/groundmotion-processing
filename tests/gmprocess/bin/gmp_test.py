#!/usr/bin/env python
import io
import os
import shutil


def test_gmp(script_runner):
    try:
        # Need to create profile first.
        setup_inputs = io.StringIO("test\n\n\nname\nemail\n")
        ret = script_runner.run('gmp', 'projects', '-c', stdin=setup_inputs)
        assert ret.success

        ret = script_runner.run('gmp', '--version')
        assert ret.success

        ret = script_runner.run('gmp', '--help')
        assert ret.success
    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree('pytest_gmp_proj_dir')


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_gmp()
