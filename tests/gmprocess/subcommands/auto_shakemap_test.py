#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import shutil

from gmprocess.utils import constants


def test_auto_shakemap(script_runner):
    try:
        # Need to create profile first.
        cdir = str(constants.CONFIG_PATH_TEST)
        ddir = str(constants.TEST_DATA_DIR / "demo")
        setup_inputs = io.StringIO(f"test\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run(
            "gmrecords", "auto_shakemap", "-e", "ci38457511", "--skip-download"
        )
        assert ret.success

        events = ["ci38457511"]
        out_names = ["workspace.h5"]
        for event in events:
            for outname in out_names:
                dfile = os.path.join(ddir, event, outname)
                print(dfile)
                assert os.path.isfile(dfile)

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST)
        # Remove workspace and image files
        pattern = ["workspace.h5", ".png", ".csv", "_dat.json", "_metrics.json"]
        for root, _, files in os.walk(ddir):
            for file in files:
                if any(file.endswith(ext) for ext in pattern):
                    os.remove(os.path.join(root, file))


if __name__ == "__main__":
    test_auto_shakemap()
