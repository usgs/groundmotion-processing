#!/usr/bin/env python

# stdlib imports
import os
import shutil

# third party imports
import pkg_resources

from impactutils.io.cmd import get_command_output


def test_demo_data():
    gmprocess = pkg_resources.resource_filename(
        'gmprocess', os.path.join('..', 'bin', 'gmprocess'))

    data_dir = pkg_resources.resource_filename(
        'gmprocess', os.path.join('data', 'testdata', 'demo'))
    out_dir = 'temp_dir'

    # Assemble
    try:
        cmd = ('%s -o %s --assemble --directory %s'
               % (gmprocess, out_dir, data_dir))
        rc, so, se = get_command_output(cmd)
        assert rc

        cmd = ('%s -o %s --process'
               % (gmprocess, out_dir))
        rc, so, se = get_command_output(cmd)
        assert rc

        cmd = ('%s -o %s --report'
               % (gmprocess, out_dir))
        rc, so, se = get_command_output(cmd)

        cmd = ('%s -o %s --export'
               % (gmprocess, out_dir))
        rc, so, se = get_command_output(cmd)

        assert rc

    except Exception as e:
        raise e
    finally:
        shutil.rmtree(out_dir)


if __name__ == '__main__':
    test_demo_data()
