#!/usr/bin/env pytest
# -*- coding: utf-8 -*-

# stdlib imports
import os
import shutil

from impactutils.io.cmd import get_command_output


def test_gmsetup():

    out_dir = 'temp_dir'

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    try:
        # Create config file:
        fname = os.path.join(out_dir, 'test.yml')
        cmd = ('gmsetup %s -f %s -e %s'
               % (fname,
                  'Test User',
                  'test@email.com')
               )

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
    test_gmsetup()
