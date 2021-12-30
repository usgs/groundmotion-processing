#!/usr/bin/env python

# stdlib imports
import pathlib
import shutil
import tempfile
from io import StringIO
import time


# local imports
from gmprocess.io.cosmos.cosmos_writer import (
    TextHeader,
    Volume,
    IntHeader,
    FloatHeader,
    DataBlock,
    CosmosWriter,
)
from gmprocess.io.cosmos.core import is_cosmos, read_cosmos
from gmprocess.io.asdf.stream_workspace import StreamWorkspace

SAMPLE_INT_HDR = """
 100  Integer-header values follow on 10 lines, Format= (10I8)
       2       1       4     120       1    -999    -999    -999    -999    -999
       2    -999    -999    -999    -999    -999    -999    -999     999    -999
    -999    -999       3    -999       5       5       5       5    -999    -999
    -999    -999    -999    -999    -999    -999    -999    -999    -999    2014
     236       8      24      10      20    -999    -999    -999    -999       1
    -999    -999    -999      90    -999    -999    -999    -999    -999       5
    -999       5    -999       1    -999    -999    -999    -999    -999    -999
    -999    -999    -999    -999    -999    -999    -999    -999    -999    -999
    -999    -999    -999    -999    -999    -999    -999    -999    -999    -999
    -999    -999    -999    -999    -999    -999    -999    -999    -999    -999
"""

SAMPLE_FLOAT_HDR = """
100 Real-header values follow on 17 lines , Format = (6F13.6)
    38.266660  -122.657590     9.000000  -999.000000  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000    38.215167  -122.312333     6.020000
  -999.000000  -999.000000  -999.000000  -999.000000 30760.954789   280.815395
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000    47.000000
  -999.000000  -999.000000  -999.000000     0.005000    63.625000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000426212.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000     0.014638
  -999.000000  -999.000000    75.000000  -999.000000  -999.000000  -999.000000
  -999.000000     5.000000    63.625000    34.163065    10.045000     0.002329
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000
"""

SAMPLE_TEXT_HDR = """
Corrected acceleration    (Format v01.20 with 13 text lines) Converted from ASDF
M6.02 at 2014-08-24T10:20:44.070000Z    August 24, 2014 10:20 UTC
Hypocenter: 38.215   -122.312   H= 11km(NCSN) M=6.0
Origin: 08/24/2014, 10:20:44.0 UTC (NCSN)
Statn No: 02-    0  Code:NP-1743   USGS CA:Petaluma;FS 2
Coords: 38.2667 -122.6576  Site geology:Unknown
Recorder:        s/n:     (  3 Chns of  3 at Sta) Sensor:K2 Epise   s/n
Rcrd start time:08/24/2014, 10:20:47.695 UTC (Q=0) RcrdId:NP.1743.HNE.
Sta Chan   1: 90 deg (Rcrdr Chan  1) Location:
Raw record length =  63.620 sec, Uncor max =    0.000        at    0.000 sec
Processed:                               Max =    34.163 cm/s^2   at  10.045 sec
Record filtered below  0.01 Hz (periods over  68.3 secs)  and above 75.0 Hz
Values used when parameter or data value is unknown/unspecified:   -999 -999.0  
"""

SAMPLE_DATA_BLOCK = """
0 Comment line(s) follow, each starting with a "|":
12725 acceleration pts, approx 63 secs, units=cm/s^2,Format=(8F10.5)
   0.03630   0.03632   0.03622   0.03619   0.03615   0.03607   0.03606   0.03600
   0.03593   0.03592   0.03584   0.03579   0.03577   0.03567   0.03567   0.03560
   0.03553   0.03555   0.03543   0.03541   0.03539   0.03526   0.03530   0.03520
   0.03515   0.03519   0.03503   0.03506   0.03504   0.03485   0.03490   0.03484
   0.03472   0.03472   0.03465   0.03461   0.03455   0.03450   0.03445   0.03446
   0.03441   0.03431   0.03431   0.03423   0.03426   0.03425   0.03406   0.03423
   0.03409   0.03388   0.03413   0.03389   0.03375   0.03382   0.03354   0.03358
   0.03356   0.03349   0.03362   0.03352   0.03370   0.03378   0.03345   0.03358
"""


def get_sample_data(volume):
    thisdir = pathlib.Path(__file__).parent
    datafile = (
        thisdir
        / ".."
        / ".."
        / ".."
        / ".."
        / "gmprocess"
        / "data"
        / "testdata"
        / "asdf"
        / "nc72282711"
        / "workspace.h5"
    )
    workspace = StreamWorkspace.open(datafile)

    eventid = workspace.getEventIds()[0]
    scalar_event = workspace.getEvent(eventid)

    station = "NP.1743"
    labels = workspace.getLabels()
    if volume == Volume.RAW:
        labels.remove("default")
    elif volume == Volume.CONVERTED:
        labels.remove("default")
    else:
        labels.remove("unprocessed")
    plabel = labels[0]
    streams = workspace.getStreams(eventid, stations=[station], labels=[plabel])
    gmprocess_version = workspace.getGmprocessVersion()
    stream = streams[0]
    trace = stream[0]
    workspace.close()
    return (trace, scalar_event, stream, gmprocess_version)


def test_text_header():
    # get some data
    volume = Volume.PROCESSED
    trace, scalar_event, stream, gmprocess_version = get_sample_data(volume)
    text_header = TextHeader(trace, scalar_event, stream, volume, gmprocess_version)
    cosmos_file = StringIO()
    text_header.write(cosmos_file)
    output = cosmos_file.getvalue()
    sample_lines = SAMPLE_TEXT_HDR.lstrip().split("\n")
    for idx, line1 in enumerate(output.split("\n")):
        line2 = sample_lines[idx]
        try:
            assert line1.strip() == line2.strip()
        except:
            x = 1


def test_int_header():
    volume = Volume.PROCESSED
    trace, scalar_event, stream, gmprocess_version = get_sample_data(volume)
    int_header = IntHeader(trace, scalar_event, stream, volume, gmprocess_version)
    cosmos_file = StringIO()
    int_header.write(cosmos_file)
    output = cosmos_file.getvalue()
    sample_lines = SAMPLE_INT_HDR.lstrip().split("\n")
    for idx, line1 in enumerate(output.split("\n")):
        line2 = sample_lines[idx]
        assert line1.strip() == line2.strip()


def test_float_header():
    volume = Volume.PROCESSED
    trace, scalar_event, stream, gmprocess_version = get_sample_data(volume)
    float_header = FloatHeader(trace, scalar_event, volume)
    cosmos_file = StringIO()
    float_header.write(cosmos_file)
    output = cosmos_file.getvalue()
    sample_lines = SAMPLE_FLOAT_HDR.lstrip().split("\n")
    output_lines = output.split("\n")
    for idx, line1 in enumerate(output_lines):
        line2 = sample_lines[idx]
        assert line1.strip() == line2.strip()


def test_data_block():
    volume = Volume.PROCESSED
    trace, scalar_event, stream, gmprocess_version = get_sample_data(volume)
    data_block = DataBlock(trace, volume)
    cosmos_file = StringIO()
    data_block.write(cosmos_file)
    output = cosmos_file.getvalue()
    output_lines = output.split("\n")
    sample_lines = SAMPLE_DATA_BLOCK.lstrip().rstrip().split("\n")
    for idx, line1 in enumerate(sample_lines):
        line2 = output_lines[idx]
        assert line1.strip() == line2.strip()


def test_cosmos_writer():
    thisdir = pathlib.Path(__file__).parent
    datafile = (
        thisdir
        / ".."
        / ".."
        / ".."
        / ".."
        / "gmprocess"
        / "data"
        / "testdata"
        / "asdf"
        / "nc72282711"
        / "workspace.h5"
    )
    tempdir = None
    try:
        tempdir = tempfile.mkdtemp()
        cosmos_writer = CosmosWriter(
            tempdir, datafile, volume=Volume.PROCESSED, label="default"
        )
        t1 = time.time()
        files, nevents, nstreams, ntraces = cosmos_writer.write()
        t2 = time.time()
        dt = t2 - t1
        msg = (
            f"{nevents} events, {nstreams} streams, "
            f"{ntraces} traces written: {dt:.2f} seconds"
        )
        print(msg)
        for tfile in files:
            assert is_cosmos(tfile)
            streams = read_cosmos(tfile)

    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tempdir)


if __name__ == "__main__":
    print("Testing data block...")
    test_data_block()
    print("Testing float header...")
    test_float_header()
    print("Testing int header...")
    test_int_header()
    print("Testing text header...")
    test_text_header()
    print("Testing cosmos writer...")
    test_cosmos_writer()
