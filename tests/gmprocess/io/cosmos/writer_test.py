#!/usr/bin/env python

# stdlib imports
import pathlib
import shutil
import tempfile
from io import StringIO
import sys
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
       5    -999    -999    -999    -999    -999    -999    -999     999    -999
    -999    -999       3    -999       5       5       5       5    -999    -999
    -999    -999    -999    -999    -999    -999    -999    -999    -999    2021
     354      12      20      20      13    -999    -999    -999    -999       1
    -999    -999    -999     270    -999    -999    -999    -999    -999       5
    -999       5    -999       1    -999    -999    -999    -999    -999    -999
    -999    -999    -999    -999    -999    -999    -999    -999    -999    -999
    -999    -999    -999    -999    -999    -999    -999    -999    -999    -999
    -999    -999    -999    -999    -999    -999    -999    -999    -999    -999
"""

SAMPLE_FLOAT_HDR = """
100 Real-header values follow on 17 lines , Format = (6F13.6)
    39.923300  -123.761400   245.000000  -999.000000  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000    40.349833  -124.899333     4.840000
  -999.000000  -999.000000  -999.000000  -999.000000   107.924360   115.661748
  -999.000000  -999.000000  -999.000000     0.596046  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000    55.000000
  -999.000000  -999.000000  -999.000000     0.010000   120.910000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000     1.254271
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000     0.656950
  -999.000000  -999.000000    12.940812  -999.000000  -999.000000  -999.000000
  -999.000000    10.000000   120.910000    -0.587939    17.080000    -0.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000
  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000  -999.000000
"""

SAMPLE_TEXT_HDR = """
Corrected acceleration    (Format v01.20 with 13 text lines) Converted from ASDF
M4.84 at 2021-12-20T20:13:40.750000Z                                            
Hypocenter: 40.350   -124.899   H= 20km(NCSN) M=4.8                             
Origin: 12/20/2021, 20:13:40.7 UTC (NCSN)                                       
Statn No: 05-    0  Code:CE-79435  CGS  Leggett - Confusion Hill Bridge Grnds   
Coords: 39.9233 -123.7614  Site geology:Unknown                                 
Recorder:        s/n:     (  3 Chns of  3 at Sta) Sensor:Kinemetr   s/n         
Rcrd start time:12/20/2021, 20:13:55.850 UTC (Q= ) RcrdId:CE.79435.HNE.10       
Sta Chan   1:270 deg (Rcrdr Chan  1) Location:10                               
Raw record length = 120.900 sec, Uncor max =    0.000        at    0.000 sec    
Processed:                               Max =    -0.588 cm/s^2   at  17.080 sec
Record filtered below  0.66 Hz (periods over   1.5 secs)  and above 12.9 Hz     
Values used when parameter or data value is unknown/unspecified:   -999 -999.0  
"""

SAMPLE_DATA_BLOCK = """
4 Comment line(s) follow, each starting with a "|":                             
| Sensor: Kinemetrics_Episensor                                                 
| RcrdId: NC.71126864.CE.79435.HNE.10                                            
| SCNL: 79435.HNE.CE.10                                                         
|<PROCESS>Automatically processed using gmprocess version 1.1.11                
12091 acceleration pts, approx 120 secs, units=cm/s^2,Format=(8F10.5)           
  -0.00003  -0.00004  -0.00004  -0.00004  -0.00004  -0.00004  -0.00004  -0.00004
  -0.00004  -0.00004  -0.00003  -0.00003  -0.00003  -0.00003  -0.00003  -0.00003
  -0.00002  -0.00002  -0.00002  -0.00002  -0.00003  -0.00003  -0.00002  -0.00002
  -0.00001  -0.00002  -0.00002  -0.00003  -0.00002  -0.00001   0.00001   0.00002
   0.00002   0.00001   0.00001   0.00001   0.00002   0.00005   0.00007   0.00007
   0.00007   0.00005   0.00003   0.00003   0.00004   0.00005   0.00006   0.00005
   0.00004   0.00004   0.00006   0.00010   0.00015   0.00019   0.00018   0.00015
   0.00011   0.00008   0.00010   0.00014   0.00017   0.00019   0.00018   0.00015
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
        / "nc71126864"
        / "workspace.h5"
    )
    workspace = StreamWorkspace.open(datafile)
    t1 = time.time()
    eventid = workspace.getEventIds()[0]
    t2 = time.time()
    print(f"{t2-t1:.2f} seconds to read eventid")
    scalar_event = workspace.getEvent(eventid)

    station = "CE.79435"
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
    idx = gmprocess_version.find(".dev")
    gmprocess_version = gmprocess_version[0:idx]
    stream = streams[0]
    trace = stream[0]
    workspace.close()
    return (trace, eventid, scalar_event, stream, gmprocess_version)


def test_text_header():
    # get some data
    volume = Volume.PROCESSED
    trace, eventid, scalar_event, stream, gmprocess_version = get_sample_data(volume)
    text_header = TextHeader(trace, scalar_event, stream, volume, gmprocess_version)
    cosmos_file = StringIO()
    text_header.write(cosmos_file)
    output = cosmos_file.getvalue()
    sample_lines = SAMPLE_TEXT_HDR.lstrip().split("\n")
    for idx, line1 in enumerate(output.split("\n")):
        line2 = sample_lines[idx]
        assert line1.strip() == line2.strip()


def test_int_header():
    volume = Volume.PROCESSED
    trace, eventid, scalar_event, stream, gmprocess_version = get_sample_data(volume)
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
    trace, eventid, scalar_event, stream, gmprocess_version = get_sample_data(volume)
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
    trace, eventid, scalar_event, stream, gmprocess_version = get_sample_data(volume)
    data_block = DataBlock(trace, volume, eventid, gmprocess_version)
    cosmos_file = StringIO()
    data_block.write(cosmos_file)
    output = cosmos_file.getvalue()
    output_lines = output.split("\n")
    sample_lines = SAMPLE_DATA_BLOCK.lstrip().rstrip().split("\n")
    for idx, line1 in enumerate(sample_lines):
        line2 = output_lines[idx]
        assert line1.strip() == line2.strip()


def test_cosmos_writer(datafile=None):
    if datafile is None:
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
            / "nc71126864"
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
            try:
                assert is_cosmos(tfile)
            except:
                x = 1
            streams = read_cosmos(tfile)

    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tempdir)


if __name__ == "__main__":
    datafile = None
    if len(sys.argv) > 1:
        datafile = sys.argv[1]
    print("Testing text header...")
    test_text_header()

    print("Testing int header...")
    test_int_header()

    print("Testing float header...")
    test_float_header()

    print("Testing data block...")
    test_data_block()

    print("Testing cosmos writer...")
    test_cosmos_writer(datafile)
