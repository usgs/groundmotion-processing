#!/usr/bin/env python
import io
import os
import shutil
import pkg_resources


def test_export_regression_plot(script_runner):
    try:
        # Need to create profile first.
        cdir = 'pytest_gmp_proj_dir'
        ddir = pkg_resources.resource_filename(
            'gmprocess', os.path.join('data', 'testdata',
                                      'demo_steps', 'exports'))
        setup_inputs = io.StringIO(
            "test\n%s\n%s\nname\nemail\n" % (cdir, ddir)
        )
        ret = script_runner.run('gmp', 'projects', '-c', stdin=setup_inputs)
        assert ret.success

        ret = script_runner.run('gmp', 'export_metric_tables')

        ret = script_runner.run('gmp', 'regression')
        assert ret.success

        # Check that files were created
        count = 0
        pattern = 'regression_'
        for root, _, files in os.walk(ddir):
            for file in files:
                if pattern in file:
                    count += 1
        assert count == 1

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree('pytest_gmp_proj_dir')
        # Remove created files
        patterns = ['_metrics_', '_events.',
                    '_fit_spectra_parameters', 'regression_']
        for root, _, files in os.walk(ddir):
            for file in files:
                for pattern in patterns:
                    if pattern in file:
                        os.remove(os.path.join(root, file))


if __name__ == '__main__':
    test_export_regression_plot()
