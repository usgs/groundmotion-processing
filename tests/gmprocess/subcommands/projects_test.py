#!/usr/bin/env python
import io
import shutil


def test_projects(script_runner):
    try:
        # Need to create profile first.
        setup_inputs = io.StringIO("test\n\n\nname\nemail\n")
        ret = script_runner.run('gmp', 'projects', '-c', stdin=setup_inputs)
        assert ret.success

        ret = script_runner.run('gmp', 'projects', '-h')
        assert ret.success

        setup_inputs = io.StringIO("test2\n\n\nname\nemail\n")
        ret = script_runner.run('gmp', 'projects', '-c', stdin=setup_inputs)
        assert ret.success

        ret = script_runner.run('gmp', 'projects', '-l')
        assert ret.success
        assert 'Project: test2 **Current Project**' in ret.stdout

        ret = script_runner.run('gmp', 'projects', '-s', 'test')
        assert ret.success

        setup_inputs = io.StringIO("y\n")
        ret = script_runner.run(
            'gmp', 'projects', '-d', 'test2', stdin=setup_inputs)
        assert ret.success
        assert 'Project: test2' not in ret.stdout

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree('pytest_gmp_proj_dir')


if __name__ == '__main__':
    test_projects()
