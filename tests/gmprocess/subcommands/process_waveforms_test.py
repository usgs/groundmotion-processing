#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import shutil

from gmprocess.utils import constants


def test_process_waveforms(script_runner):
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = str(constants.DATA_DIR / "testdata" / "demo_steps" / "process_waveforms")

        # Make a copy of the hdf files
        events = ["ci38038071", "ci38457511"]
        for event in events:
            src = os.path.join(ddir, event, "workspace.h5")
            dst = os.path.join(ddir, event, "_workspace.h5")
            shutil.copyfile(src, dst)

        setup_inputs = io.StringIO(f"2\ntest\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run("gmrecords", "process_waveforms")
        assert ret.success

        # No new files created, check stderr
        assert "Finished processing streams." in ret.stderr
        assert "Adding waveforms for station AZ.HSSP" in ret.stderr
        assert "Adding waveforms for station CE.23178" in ret.stderr
        assert "Adding waveforms for station CE.23837" in ret.stderr
        assert "Adding waveforms for station CI.CCC" in ret.stderr
        assert "Adding waveforms for station CI.CLC" in ret.stderr
        assert "Adding waveforms for station CI.TOW2" in ret.stderr

        ret = script_runner.run(
            "gmrecords", "process_waveforms", "-n", "2", "-l", "dasktest"
        )
        assert ret.success

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST)
        # Move the hdf files back
        events = ["ci38038071", "ci38457511"]
        for event in events:
            dst = os.path.join(ddir, event, "workspace.h5")
            src = os.path.join(ddir, event, "_workspace.h5")
            shutil.move(src, dst)


if __name__ == "__main__":
    test_process_waveforms()
