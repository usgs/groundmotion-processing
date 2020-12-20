#!/usr/bin/env python

# stdlib imports
import pathlib
import shutil
import tempfile
import json

# local imports
from gmprocess.io.fetch_utils import save_shakemap_amps
from gmprocess.io.asdf.stream_workspace import StreamWorkspace


def test_get_shakemap():
    tdir = tempfile.mkdtemp()
    try:
        thisdir = pathlib.Path(__file__).parent
        datadir = (thisdir / '..' / '..' / '..' / 'gmprocess'
                   / 'data' / 'testdata')
        datafile = datadir / 'workspace_ci38457511.hdf'

        workspace = StreamWorkspace.open(datafile)
        eventid = workspace.getEventIds()[0]
        event = workspace.getEvent(eventid)
        label = '20201209195000'
        processed = workspace.getStreams(eventid, labels=[label])

        excelfile, jsonfile = save_shakemap_amps(processed, event, tdir)
        with open(jsonfile, 'rt') as fp:
            jdict = json.load(fp)
        assert jdict['features'][0]['id'] == 'CJ.T001230'

    except Exception as e:
        raise AssertionError(str(e))
    finally:
        shutil.rmtree(tdir)


if __name__ == '__main__':
    test_get_shakemap()
