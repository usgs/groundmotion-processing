#!/usr/bin/env pytest
# -*- coding: utf-8 -*-

# stdlib imports
import os
import shutil

# third party imports
import pkg_resources

from impactutils.io.cmd import get_command_output


def test_gminfo():
    data_dir = pkg_resources.resource_filename(
        "gmprocess", os.path.join("data", "testdata", "demo", "ci38457511", "raw")
    )
    out_dir = "temp_dir"

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    try:
        # Concise output, save to file
        cmd = f"gminfo {data_dir} -c -s {os.path.join(out_dir, 'test.csv')}"

        rc, so, se = get_command_output(cmd)
        assert rc

        # Verbose output
        cmd = f"gminfo {data_dir}"
        rc, so, se = get_command_output(cmd)
        assert rc
        assert "Caltech" in so.decode()
        assert "CLC" in so.decode()

    except Exception as e:
        print(so.decode())
        print(se.decode())
        raise e
    finally:
        shutil.rmtree(out_dir)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_gminfo()
