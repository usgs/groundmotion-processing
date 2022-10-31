#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import shutil
import pathlib

from gmprocess.utils import constants


def test_import(script_runner):
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = constants.TEST_DATA_DIR / "demo"
        idir = constants.TEST_DATA_DIR / "import"

        setup_inputs = io.StringIO(
            f"test\n{str(cdir)}\n{str(ddir)}\nname\ntest@email.com\n"
        )
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        # Test CESMD zip file
        zfile = idir / "cesmd_test.zip"
        ret = script_runner.run(
            "gmrecords", "-e", "nn00725272", "import", "-p", str(zfile)
        )
        print("*** stdout ***")
        print(ret.stdout)
        print("*** stderr ***")
        print(ret.stderr)
        assert ret.success
        raw_dir = ddir / "nn00725272" / "raw"
        assert raw_dir.is_dir()
        dst_files = list(pathlib.Path(raw_dir).glob("*"))
        assert len(dst_files) == 23

        # Test tar file of CWB data
        tfile = idir / "test.tar.zip"
        ret = script_runner.run(
            "gmrecords", "-e", "us6000e2mt", "import", "-p", str(tfile)
        )
        assert ret.success
        raw_dir = ddir / "us6000e2mt" / "raw"
        assert raw_dir.is_dir()
        dst_dats = list(raw_dir.glob("*.dat"))
        assert len(dst_dats) == 19

        # Test directory of files
        dpath = idir / "dir"
        ret = script_runner.run(
            "gmrecords", "-e", "us6000e2mt", "import", "-p", str(dpath)
        )
        assert ret.success

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(str(constants.CONFIG_PATH_TEST), ignore_errors=True)
        # Remove created files
        events = ["us6000e2mt", "nn00725272"]
        for eid in events:
            shutil.rmtree(str(ddir / eid), ignore_errors=True)


if __name__ == "__main__":
    test_import()
