#!/usr/bin/env pytest
# -*- coding: utf-8 -*-

import os
import shutil

from esi_utils_io.cmd import get_command_output
from gmprocess.utils.constants import DATA_DIR


def test_gminfo():
    input_dir = DATA_DIR / "testdata" / "geonet"
    out_dir = "temp_dir"

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    try:
        # Concise output, save to file
        cmd = f"gminfo {input_dir} -c -s {os.path.join(out_dir, 'test.csv')}"

        rc, so, se = get_command_output(cmd)
        assert rc

        # Verbose output
        cmd = f"gminfo {input_dir}"
        rc, so, se = get_command_output(cmd)
        assert rc
        assert "New Zealand Institute of Geological and Nuclear Science" in so.decode()
        assert "HSES" in so.decode()

    except Exception as e:
        print(so.decode())
        print(se.decode())
        raise e
    finally:
        shutil.rmtree(out_dir)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_gminfo()
