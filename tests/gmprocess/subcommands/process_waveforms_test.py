#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import shutil
import pkg_resources

from gmprocess.utils import constants


def test_process_waveforms(script_runner):
    try:
        # Need to create profile first.
        cdir = constants.PROJECTS_PATH_TEST
        ddir = pkg_resources.resource_filename(
            'gmprocess', os.path.join('data', 'testdata',
                                      'demo_steps', 'process_waveforms'))

        # Make a copy of the hdf files
        events = ['ci38038071', 'ci38457511']
        for event in events:
            src = os.path.join(ddir, event, 'workspace.h5')
            dst = os.path.join(ddir, event, '_workspace.h5')
            shutil.copyfile(src, dst)

        setup_inputs = io.StringIO(
            "test\n%s\n%s\nname\nemail\n" % (cdir, ddir)
        ).encode('utf-8')
        ret = script_runner.run('gmp', 'projects', '-c', stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run('gmp', 'process_waveforms')
        assert ret.success

        # No new files created, check stderr
        assert 'Finished processing streams.' in ret.stderr
        assert 'Adding waveforms for station HSSP' in ret.stderr
        assert 'Adding waveforms for station 23178' in ret.stderr
        assert 'Adding waveforms for station 23837' in ret.stderr
        assert 'Adding waveforms for station CCC' in ret.stderr
        assert 'Adding waveforms for station CLC' in ret.stderr
        assert 'Adding waveforms for station TOW2' in ret.stderr

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.PROJECTS_PATH_TEST)
        # Move the hdf files back
        events = ['ci38038071', 'ci38457511']
        for event in events:
            dst = os.path.join(ddir, event, 'workspace.h5')
            src = os.path.join(ddir, event, '_workspace.h5')
            shutil.move(src, dst)


if __name__ == '__main__':
    test_process_waveforms()
