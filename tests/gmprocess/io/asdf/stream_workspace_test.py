#!/usr/bin/env python

import os.path
import shutil
import time
import tempfile

from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.read import read_data
from gmprocess.processing import process_streams
from gmprocess.config import get_config
from gmprocess.io.test_utils import read_data_dir
from gmprocess.event import get_event_object
from gmprocess.streamcollection import StreamCollection
from gmprocess.metrics.station_summary import StationSummary
import numpy as np
import pandas as pd


def compare_streams(instream, outstream):
    pkeys = instream[0].getParameterKeys()
    for key in pkeys:
        if not outstream[0].hasParameter(key):
            assert 1 == 2
        invalue = instream[0].getParameter(key)
        outvalue = outstream[0].getParameter(key)
        assert invalue == outvalue

    # compare the provenance from the input processed stream
    # to it's output equivalent
    pkeys = instream[0].getProvenanceKeys()
    for key in pkeys:
        inprov = instream[0].getProvenance(key)[0]
        outprov = outstream[0].getProvenance(key)[0]
        for key, invalue in inprov.items():
            outvalue = outprov[key]
            if isinstance(invalue, (int, float, str)):
                assert invalue == outvalue
            else:
                assert np.abs(invalue - outvalue) < 1


def test_workspace():
    eventid = 'us1000778i'
    datafiles, origin = read_data_dir('geonet', eventid, '*.V1A')
    event = get_event_object(origin)
    tdir = tempfile.mkdtemp()
    try:
        config = get_config()
        tfile = os.path.join(tdir, 'test.hdf')
        raw_streams = []
        for dfile in datafiles:
            raw_streams += read_data(dfile)

        workspace = StreamWorkspace(tfile)
        t1 = time.time()
        workspace.addStreams(event, raw_streams, label='raw')
        t2 = time.time()
        print('Adding %i streams took %.2f seconds' %
              (len(raw_streams), (t2 - t1)))

        str_repr = workspace.__repr__()
        assert str_repr == 'Events: 1 Stations: 3 Streams: 3'

        stations = workspace.getStations()
        assert sorted(stations) == ['hses', 'thz', 'wtmc']

        eventobj = workspace.getEvent(eventid)
        assert eventobj.origins[0].latitude == event.origins[0].latitude
        assert eventobj.magnitudes[0].mag == event.magnitudes[0].mag

        # test retrieving tags for an event that doesn't exist
        try:
            workspace.getStreamTags('foo')
        except KeyError:
            assert 1 == 1

        # test retrieving event that doesn't exist
        try:
            workspace.getEvent('foo')
        except KeyError:
            assert 1 == 1

        instream = None
        for stream in raw_streams:
            if stream[0].stats.station.lower() == 'hses':
                instream = stream
                break
        if instream is None:
            assert 1 == 2
        outstream = workspace.getStreams(eventid,
                                         stations=['hses'],
                                         labels=['raw'])[0]
        compare_streams(instream, outstream)

        label_summary = workspace.summarizeLabels()
        assert label_summary.iloc[0]['Label'] == 'raw'
        assert label_summary.iloc[0]['Software'] == 'gmprocess'

        sc = StreamCollection(raw_streams)
        processed_streams = process_streams(sc, origin, config=config)
        workspace.addStreams(event, processed_streams, 'processed')

        idlist = workspace.getEventIds()
        assert idlist[0] == eventid

        event_tags = workspace.getStreamTags(eventid)
        assert event_tags == ['hses_processed', 'hses_raw',
                              'thz_processed', 'thz_raw',
                              'wtmc_processed', 'wtmc_raw']
        outstream = workspace.getStreams(eventid,
                                         stations=['hses'],
                                         labels=['processed'])[0]

        # compare the parameters from the input processed stream
        # to it's output equivalent
        instream = None
        for stream in processed_streams:
            if stream[0].stats.station.lower() == 'hses':
                instream = stream
                break
        if instream is None:
            assert 1 == 2
        compare_streams(instream, outstream)
        workspace.close()

        # read in data from a second event and stash it in the workspace
        eventid = 'nz2018p115908'
        datafiles, origin = read_data_dir('geonet', eventid, '*.V2A')
        raw_streams = []
        for dfile in datafiles:
            raw_streams += read_data(dfile)

        event = get_event_object(origin)
        workspace = StreamWorkspace.open(tfile)
        workspace.addStreams(event, raw_streams, label='foo')

        eventids = workspace.getEventIds()
        assert eventids == ['us1000778i', 'nz2018p115908']
        instation = raw_streams[0][0].stats.station
        this_stream = workspace.getStreams(eventid,
                                           stations=[instation],
                                           labels=['foo'])[0]
        assert instation == this_stream[0].stats.station

        # set and retrieve waveform metrics in the file
        imclist = ['greater_of_two_horizontals',
                   'channels',
                   'rotd50',
                   'rotd100']
        imtlist = ['sa1.0', 'PGA', 'pgv', 'fas2.0', 'arias']
        usid = 'us1000778i'
        tags = workspace.getStreamTags(usid)
        workspace.setStreamMetrics(eventid, labels=['processed'],
                                   imclist=imclist, imtlist=imtlist)
        stream2 = workspace.getStreamMetrics(usid, tags[0])
        pass

    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tdir)


if __name__ == '__main__':
    test_workspace()
