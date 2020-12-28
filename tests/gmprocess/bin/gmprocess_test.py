#!/usr/bin/env python

# stdlib imports
import os
import shutil

# third party imports
import pkg_resources

from impactutils.io.cmd import get_command_output


def test_demo_data():
    data_dir = pkg_resources.resource_filename(
        'gmprocess', os.path.join('data', 'testdata', 'demo'))
    out_dir = 'temp_dir'

    try:
        cmd = ('gmprocess2 -o %s --assemble --directory %s'
               % (out_dir, data_dir))
        rc, so, se = get_command_output(cmd)
        assert rc

        cmd = ('gmprocess2 -o %s --process' % out_dir)
        rc, so, se = get_command_output(cmd)
        assert rc

        cmd = ('gmprocess2 -o %s --report' % out_dir)
        rc, so, se = get_command_output(cmd)
        print(so.decode())
        print(se.decode())
        assert rc

        cmd = ('gmprocess2 -o %s --export' % out_dir)
        rc, so, se = get_command_output(cmd)
        assert rc

        cmd = ('gmprocess2 -o %s --provenance' % out_dir)
        rc, so, se = get_command_output(cmd)
        assert rc

    except Exception as e:
        print(so.decode())
        print(se.decode())
        raise e
    finally:
        shutil.rmtree(out_dir)


def test_eventfile():
    out_dir = 'temp_dir'

    conf_file = pkg_resources.resource_filename(
        'gmprocess', os.path.join('data', 'testdata', 'conf_small.yml'))

    eventfile = pkg_resources.resource_filename(
        'gmprocess', os.path.join('data', 'testdata', 'example_eventfile.txt'))

    try:
        cmd = ('gmprocess2 -o %s --assemble --textfile %s --config %s'
               % (out_dir, eventfile, conf_file))
        rc, so, se = get_command_output(cmd)
        assert rc

    except Exception as e:
        print(so.decode())
        print(se.decode())
        raise e
    finally:
        shutil.rmtree(out_dir)


def test_parallel():
    data_dir = pkg_resources.resource_filename(
        'gmprocess', os.path.join('data', 'testdata', 'demo'))
    out_dir = 'temp_dir'

    try:
        cmd = ('gmprocess2 -o %s --assemble --directory %s -n 2'
               % (out_dir, data_dir))
        rc, so, se = get_command_output(cmd)
        assert rc

    except Exception as e:
        print(so.decode())
        print(se.decode())
        raise e
    finally:
        shutil.rmtree(out_dir)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_demo_data()
    test_eventfile()
    test_parallel()
