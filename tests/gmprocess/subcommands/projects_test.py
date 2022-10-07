#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import shutil

from gmprocess.utils import constants


def test_projects(script_runner):
    try:
        # Need to create profile first.
        setup_inputs = io.StringIO("test1\n\n\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run("gmrecords", "projects", "-h")
        assert ret.success

        setup_inputs = io.StringIO("test2\n\n\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        setup_inputs = io.StringIO("test1\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success
        assert "Project 'test1' already exists." in ret.stderr

        ret = script_runner.run("gmrecords", "projects", "-l")
        assert ret.success
        assert "Project: test1" in ret.stdout
        assert "Project: test2 **Current Project**" in ret.stdout

        ret = script_runner.run("gmrecords", "projects", "-s", "test1")
        assert ret.success
        assert "Project: test1 **Current Project**" in ret.stdout

        ret = script_runner.run("gmrecords", "projects", "--rename", "test2", "tested")
        assert ret.success
        assert "Renamed 'test2' to 'tested'." in ret.stdout

        setup_inputs = io.StringIO("y\n")
        ret = script_runner.run(
            "gmrecords", "projects", "-d", "tested", stdin=setup_inputs
        )
        setup_inputs.close()
        assert ret.success
        assert "Project: tested" not in ret.stdout
        assert "Project: test1 **Current Project**" in ret.stdout

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST)


if __name__ == "__main__":
    test_projects()
