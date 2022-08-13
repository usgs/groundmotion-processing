#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import shutil
import glob

from gmprocess.utils import constants


def test_import(script_runner):
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = str(constants.DATA_DIR / "testdata" / "demo")
        idir = str(constants.DATA_DIR / "testdata" / "import")

        setup_inputs = io.StringIO(f"2\ntest\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        # Test CESMD zip file
        zfile = os.path.join(idir, "cesmd_test.zip")
        ret = script_runner.run("gmrecords", "import", "-e", "nn00725272", "-p", zfile)
        assert ret.success
        raw_dir = os.path.join(ddir, "nn00725272", "raw")
        assert os.path.isdir(raw_dir)
        dst_zips = glob.glob(os.path.join(raw_dir, "*.zip"))
        assert len(dst_zips) == 10

        # Test tar file of CWB data (they use zip usually though)
        tfile = os.path.join(idir, "test.tar")
        ret = script_runner.run("gmrecords", "import", "-e", "us6000e2mt", "-p", tfile)
        assert ret.success
        raw_dir = os.path.join(ddir, "us6000e2mt", "raw")
        assert os.path.isdir(raw_dir)
        dst_dats = glob.glob(os.path.join(raw_dir, "*.dat"))
        assert len(dst_dats) == 103

        # Test directory of files
        dpath = os.path.join(idir, "dir")
        ret = script_runner.run("gmrecords", "import", "-e", "us6000e2mt", "-p", dpath)
        assert ret.success

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST)
        # Remove created files
        events = ["us6000e2mt", "nn00725272"]
        for e in events:
            shutil.rmtree(os.path.join(ddir, e))


if __name__ == "__main__":
    test_import()
