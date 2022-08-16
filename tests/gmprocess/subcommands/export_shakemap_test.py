#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import shutil

from gmprocess.utils import constants


def test_export_shakemap(script_runner):
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = constants.TEST_DATA_DIR / "demo_steps" / "exports"

        setup_inputs = io.StringIO(f"2\ntest\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run("gmrecords", "shakemap")
        assert ret.success

        # Check that output files are created
        events = ["ci38457511", "ci38038071"]
        out_names = ["%s_metrics.json", "%s_groundmotions_dat.json"]
        for event in events:
            for outname in out_names:
                dfile = os.path.join(ddir, event, outname % event)
                assert os.path.isfile(dfile)

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST)
        # Remove created files
        events = ["ci38457511", "ci38038071"]
        out_names = ["%s_metrics.json", "%s_groundmotions_dat.json"]
        for event in events:
            for outname in out_names:
                dfile = os.path.join(ddir, event, outname % event)
                os.remove(dfile)


if __name__ == "__main__":
    test_export_shakemap()
