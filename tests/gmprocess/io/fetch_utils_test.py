#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import os
import pathlib
import shutil
import tempfile
import json
from obspy.core.utcdatetime import UTCDateTime

# local imports
from gmprocess.io.fetch_utils import save_shakemap_amps
from gmprocess.io.fetch_utils import read_event_json_files
from gmprocess.io.asdf.stream_workspace import StreamWorkspace


def test_get_shakemap():
    tdir = tempfile.mkdtemp()
    try:
        thisdir = pathlib.Path(__file__).parent
        datadir = os.path.join(
            thisdir, os.pardir, os.pardir, os.pardir, 'gmprocess', 'data',
            'testdata')
        datafile = os.path.join(datadir, 'workspace_ci38457511.hdf')

        workspace = StreamWorkspace.open(datafile)
        eventid = workspace.getEventIds()[0]
        event = workspace.getEvent(eventid)
        label = '20201209195000'
        processed = workspace.getStreams(eventid, labels=[label])

        excelfile, jsonfile = save_shakemap_amps(processed, event, tdir)
        with open(jsonfile, 'rt', encoding='utf-8') as fp:
            jdict = json.load(fp)
        assert jdict['features'][0]['id'] == 'CJ.T001230'

    except Exception as e:
        raise AssertionError(str(e))
    finally:
        shutil.rmtree(tdir)

def test_read_event_json_files():

    thisdir = pathlib.Path(__file__).parent
    datadir = os.path.join(
            thisdir, os.pardir, os.pardir, os.pardir, 'gmprocess', 'data',
            'testdata')
    datafile = os.path.join(datadir, 'event_json', 'event.json')

    eid = 'nc51203888'
    time = UTCDateTime('2008-06-06T09:02:53.890000Z')
    mag = 3.5
    mag_type = 'mw'

    event = read_event_json_files([datafile])[0]
    assert event.id == eid
    assert event.magnitude == mag
    assert event.magnitude_type == mag_type
    assert event.time == time

if __name__ == '__main__':
    test_get_shakemap()
    test_read_event_json_files()
