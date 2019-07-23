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
        assert rc

        cmd = ('%s -o %s --export'
               % (gmprocess, out_dir))
        rc, so, se = get_command_output(cmd)
        assert rc

        cmd = ('%s -o %s --provenance'
               % (gmprocess, out_dir))
        rc, so, se = get_command_output(cmd)
        assert rc

    except Exception as e:
        print(so.decode())
        print(se.decode())
        raise e
    finally:
        shutil.rmtree(out_dir)


def test_eventfile():
    gmprocess = pkg_resources.resource_filename(
        'gmprocess', os.path.join('..', 'bin', 'gmprocess'))

    out_dir = 'temp_dir'

    conf_file = pkg_resources.resource_filename(
        'gmprocess', os.path.join('data', 'testdata', 'conf_small.yml'))

    eventfile = pkg_resources.resource_filename(
        'gmprocess', os.path.join('data', 'testdata', 'example_eventfile.txt'))

    try:
        cmd = ('%s -o %s --assemble --textfile %s --config %s'
               % (gmprocess, out_dir, eventfile, conf_file))
        rc, so, se = get_command_output(cmd)
        assert rc

    except Exception as e:
        print(so.decode())
        print(se.decode())
        raise e
    finally:
        shutil.rmtree(out_dir)


def test_parallel():
    gmprocess = pkg_resources.resource_filename(
        'gmprocess', os.path.join('..', 'bin', 'gmprocess'))

    data_dir = pkg_resources.resource_filename(
        'gmprocess', os.path.join('data', 'testdata', 'demo'))
    out_dir = 'temp_dir'

    try:
        cmd = ('%s -o %s --assemble --directory %s -n 2'
               % (gmprocess, out_dir, data_dir))
        rc, so, se = get_command_output(cmd)
        assert rc

    except Exception as e:
        print(so.decode())
        print(se.decode())
        raise e
    finally:
        shutil.rmtree(out_dir)


if __name__ == '__main__':
    test_demo_data()
    test_eventfile()
    test_parallel()
