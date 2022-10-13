#!/usr/bin/env pytest
# -*- coding: utf-8 -*-

import os
import shutil

from esi_utils_io.cmd import get_command_output
from gmprocess.utils.constants import TEST_DATA_DIR


def test_gmconvert():
    data_dir = TEST_DATA_DIR / "demo" / "ci38457511" / "raw"
    out_dir = "temp_dir"
    try:
        cmd = f"gmconvert -i {data_dir} -o {out_dir} -f SAC"
        rc, so, se = get_command_output(cmd)
        assert rc

    except Exception as e:
        print(so.decode())
        print(se.decode())
        raise e
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_gmconvert()
