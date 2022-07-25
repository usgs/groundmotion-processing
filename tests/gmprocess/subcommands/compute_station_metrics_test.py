#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import shutil
import pkg_resources

from gmprocess.utils import constants


def test_compute_station_metrics(script_runner):
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = pkg_resources.resource_filename(
            "gmprocess",
            os.path.join("data", "testdata", "demo_steps", "compute_metrics"),
        )

        # Make a copy of the hdf files
        events = ["ci38457511"]
        for event in events:
            src = os.path.join(ddir, event, "workspace.h5")
            dst = os.path.join(ddir, event, "_workspace.h5")
            shutil.copyfile(src, dst)

        setup_inputs = io.StringIO(f"2\ntest\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run("gmrecords", "compute_station_metrics")
        print(ret.stderr)
        assert ret.success

        # No new files created, check stderr
        assert "Added station metrics to workspace files with" in ret.stderr
        assert "Calculating station metrics for CI.CCC.HN" in ret.stderr

        ret = script_runner.run("gmrecords", "compute_station_metrics", "-o")
        assert ret.success

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST)
        # Move the hdf files back
        events = ["ci38457511"]
        for event in events:
            dst = os.path.join(ddir, event, "workspace.h5")
            src = os.path.join(ddir, event, "_workspace.h5")
            shutil.move(src, dst)


def test_compute_station_metrics_rupt(script_runner):
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = pkg_resources.resource_filename(
            "gmprocess",
            os.path.join("data", "testdata", "demo_steps", "compute_metrics"),
        )

        # Make a copy of the hdf files
        events = ["ci38457511_rupt"]
        for event in events:
            src = os.path.join(ddir, event, "workspace.h5")
            dst = os.path.join(ddir, event, "_workspace.h5")
            shutil.copyfile(src, dst)

        setup_inputs = io.StringIO(f"2\ntest\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run("gmrecords", "compute_station_metrics")
        print(ret.stderr)
        assert ret.success

        # No new files created, check stderr
        assert "Added station metrics to workspace files with" in ret.stderr
        assert "Calculating station metrics for CI.CCC.HN" in ret.stderr

        ret = script_runner.run("gmrecords", "compute_station_metrics", "-o")
        assert ret.success

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST)
        # Move the hdf files back
        events = ["ci38457511_rupt"]
        for event in events:
            dst = os.path.join(ddir, event, "workspace.h5")
            src = os.path.join(ddir, event, "_workspace.h5")
            shutil.move(src, dst)


if __name__ == "__main__":
    test_compute_station_metrics()
    test_compute_station_metrics_rupt()
