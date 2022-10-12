#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import shutil
from gmprocess.utils import constants

EVENTS = ["ci38038071", "ci38457511", "ci38457511_rupt"]


def test_compute_station_metrics(script_runner):
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = constants.TEST_DATA_DIR / "demo_steps" / "compute_metrics"

        # Make a copy of the hdf files
        for event in EVENTS:
            src = str(ddir / event / "workspace.h5")
            dst = str(ddir / event / "_workspace.h5")
            shutil.copyfile(src, dst)

        setup_inputs = io.StringIO(
            f"test\n{str(cdir)}\n{str(ddir)}\nname\ntest@email.com\n"
        )
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run("gmrecords", "compute_station_metrics")
        assert ret.success

        # No new files created, check stderr
        assert "Added station metrics to workspace files with" in ret.stderr
        assert "Calculating station metrics for CI.CCC.HN" in ret.stderr

        ret = script_runner.run("gmrecords", "compute_station_metrics", "-o")
        assert ret.success

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST, ignore_errors=True)
        # Move the hdf files back
        for event in EVENTS:
            dst = str(ddir / event / "workspace.h5")
            src = str(ddir / event / "_workspace.h5")
            shutil.move(src, dst)


if __name__ == "__main__":
    test_compute_station_metrics()
