#!/usr/bin/env python

import os
import shutil
import time
import tempfile
import warnings
import pkg_resources
from ruamel.yaml import YAML

from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.read import read_data
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.rupture_utils import get_rupture_file
from gmprocess.utils.config import update_config

from h5py.h5py_warnings import H5pyDeprecationWarning
from ruamel.yaml.error import YAMLError

import numpy as np
import pandas as pd
import pytest


datapath = os.path.join("data", "testdata")
datadir = pkg_resources.resource_filename("gmprocess", datapath)


def _compare_streams(instream, outstream):
    pkeys = instream[0].getParameterKeys()
    for key in pkeys:
        if not outstream[0].hasParameter(key):
            raise Exception("outstream[0] missing key.")
        invalue = instream[0].getParameter(key)
        outvalue = outstream[0].getParameter(key)
        if isinstance(invalue, (int, float, str)):
            assert invalue == outvalue
        if isinstance(invalue, dict):
            # Currenlty, we also have dictionaries with list of floats
            # as entries. This could get more complicated if we start
            # storing a wider variety of data structures...
            for k, v in invalue.items():
                if isinstance(v, list):
                    inarray = np.array(v)
                    outarray = np.array(outvalue[k])
                    np.testing.assert_allclose(inarray, outarray)

    # compare the provenance from the input processed stream
    # to it's output equivalent
    pkeys = instream[0].getProvenanceKeys()
    for key in pkeys:
        inprov = instream[0].getProvenance(key)[0]
        outprov = outstream[0].getProvenance(key)[0]
        for key, invalue in inprov.items():
            outvalue = outprov[key]
            if isinstance(invalue, (int, str)):
                assert invalue == outvalue
            elif isinstance(invalue, float):
                np.testing.assert_allclose(invalue, outvalue)
            else:
                assert np.abs(invalue - outvalue) < 1


def _test_stream_params():
    eventid = "us1000778i"
    datafiles, event = read_data_dir("geonet", eventid, "20161113_110259_WTMC_20.V1A")
    tdir = tempfile.mkdtemp()
    streams = []
    try:
        streams += read_data(datafiles[0])
        statsdict = {"name": "Fred", "age": 34}
        streams[0].setStreamParam("stats", statsdict)
        tfile = os.path.join(tdir, "test.hdf")
        workspace = StreamWorkspace(tfile)
        workspace.addEvent(event)
        workspace.addStreams(event, streams, label="stats")
        outstreams = workspace.getStreams(event.id, labels=["stats"])
        cmpdict = outstreams[0].getStreamParam("stats")
        assert cmpdict == statsdict
        workspace.close()
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tdir)


def _test_workspace():
    eventid = "us1000778i"
    datafiles, event = read_data_dir("geonet", eventid, "*.V1A")
    tdir = tempfile.mkdtemp()
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=H5pyDeprecationWarning)
            warnings.filterwarnings("ignore", category=YAMLError)
            warnings.filterwarnings("ignore", category=FutureWarning)
            config = update_config(os.path.join(datadir, "config_min_freq_0p2.yml"))
            tfile = os.path.join(tdir, "test.hdf")
            raw_streams = []
            for dfile in datafiles:
                raw_streams += read_data(dfile)

            workspace = StreamWorkspace(tfile)
            t1 = time.time()
            workspace.addStreams(event, raw_streams, label="raw")
            t2 = time.time()
            print("Adding %i streams took %.2f seconds" % (len(raw_streams), (t2 - t1)))

            str_repr = workspace.__repr__()
            assert str_repr == "Events: 1 Stations: 3 Streams: 3"

            eventobj = workspace.getEvent(eventid)
            assert eventobj.origins[0].latitude == event.origins[0].latitude
            assert eventobj.magnitudes[0].mag == event.magnitudes[0].mag

            stations = workspace.getStations()
            assert sorted(stations) == ["HSES", "THZ", "WTMC"]

            stations = workspace.getStations()
            assert sorted(stations) == ["HSES", "THZ", "WTMC"]

            # test retrieving event that doesn't exist
            with pytest.raises(KeyError):
                workspace.getEvent("foo")

            instream = None
            for stream in raw_streams:
                if stream[0].stats.station.lower() == "hses":
                    instream = stream
                    break
            if instream is None:
                raise ValueError("Instream should not be none.")
            outstream = workspace.getStreams(
                eventid, stations=["HSES"], labels=["raw"]
            )[0]
            compare_streams(instream, outstream)

            label_summary = workspace.summarizeLabels()
            assert label_summary.iloc[0]["Label"] == "raw"
            assert label_summary.iloc[0]["Software"] == "gmprocess"

            sc = StreamCollection(raw_streams)
            processed_streams = process_streams(sc, event, config=config)
            workspace.addStreams(event, processed_streams, "processed")

            idlist = workspace.getEventIds()
            assert idlist[0] == eventid

            outstream = workspace.getStreams(
                eventid, stations=["HSES"], labels=["processed"]
            )[0]

            provenance = workspace.getProvenance(eventid, labels=["processed"])
            first_row = pd.Series(
                {
                    "Record": "NZ.HSES.--.HN1_us1000778i_processed",
                    "Processing Step": "Remove Response",
                    "Step Attribute": "input_units",
                    "Attribute Value": "counts",
                }
            )

            last_row = pd.Series(
                {
                    "Record": "NZ.WTMC.--.HNZ_us1000778i_processed",
                    "Processing Step": "Lowpass Filter",
                    "Step Attribute": "number_of_passes",
                    "Attribute Value": 2,
                }
            )
            assert provenance.iloc[0].equals(first_row)
            assert provenance.iloc[-1].equals(last_row)

            # compare the parameters from the input processed stream
            # to it's output equivalent
            instream = None
            for stream in processed_streams:
                if stream[0].stats.station.lower() == "hses":
                    instream = stream
                    break
            if instream is None:
                raise ValueError("Instream should not be none.")
            compare_streams(instream, outstream)
            workspace.close()

            # read in data from a second event and stash it in the workspace
            eventid = "nz2018p115908"
            datafiles, event = read_data_dir("geonet", eventid, "*.V2A")
            raw_streams = []
            for dfile in datafiles:
                raw_streams += read_data(dfile)

            workspace = StreamWorkspace.open(tfile)
            workspace.addStreams(event, raw_streams, label="foo")

            stations = workspace.getStations()

            eventids = workspace.getEventIds()
            assert eventids == ["us1000778i", "nz2018p115908"]
            instation = raw_streams[0][0].stats.station
            this_stream = workspace.getStreams(
                eventid, stations=[instation], labels=["foo"]
            )[0]
            assert instation == this_stream[0].stats.station
            usid = "us1000778i"
            inventory = workspace.getInventory(usid)
            workspace.close()
            codes = [station.code for station in inventory.networks[0].stations]
            assert sorted(set(codes)) == ["HSES", "THZ", "WPWS", "WTMC"]

    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tdir)


def _test_metrics2():
    eventid = "usb000syza"
    datafiles, event = read_data_dir("knet", eventid, "*")
    datadir = os.path.split(datafiles[0])[0]
    raw_streams = StreamCollection.from_directory(datadir)
    config = update_config(os.path.join(datadir, "config_min_freq_0p2.yml"))
    config["metrics"]["output_imts"].append("Arias")
    config["metrics"]["output_imcs"].append("arithmetic_mean")
    # Adjust checks so that streams pass checks for this test
    newconfig = drop_processing(config, ["check_sta_lta"])
    csnr = [s for s in newconfig["processing"] if "compute_snr" in s.keys()][0]
    csnr["compute_snr"]["check"]["threshold"] = -10.0
    processed_streams = process_streams(raw_streams, event, config=newconfig)

    tdir = tempfile.mkdtemp()
    try:
        tfile = os.path.join(tdir, "test.hdf")
        workspace = StreamWorkspace(tfile)
        workspace.addEvent(event)
        workspace.addStreams(event, processed_streams, label="processed")
        workspace.calcMetrics(event.id, labels=["processed"])
        etable, imc_tables1, readmes1 = workspace.getTables("processed")
        assert "ARITHMETIC_MEAN" not in imc_tables1
        assert "ARITHMETIC_MEAN" not in readmes1
        del workspace.dataset.auxiliary_data.WaveFormMetrics
        del workspace.dataset.auxiliary_data.StationMetrics
        workspace.calcMetrics(event.id, labels=["processed"], config=config)
        etable2, imc_tables2, readmes2 = workspace.getTables("processed")
        assert "ARITHMETIC_MEAN" in imc_tables2
        assert "ARITHMETIC_MEAN" in readmes2
        assert "ARIAS" in imc_tables2["ARITHMETIC_MEAN"]
        testarray = readmes2["ARITHMETIC_MEAN"]["Column header"].to_numpy()
        assert "ARIAS" in testarray
        workspace.close()
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tdir)


def test_metrics():
    eventid = "usb000syza"
    datafiles, event = read_data_dir("knet", eventid, "*")
    datadir = os.path.split(datafiles[0])[0]
    raw_streams = StreamCollection.from_directory(datadir)
    config = update_config(os.path.join(datadir, "config_min_freq_0p2.yml"))
    # turn off sta/lta check and snr checks
    # newconfig = drop_processing(config, ['check_sta_lta', 'compute_snr'])
    # processed_streams = process_streams(raw_streams, event, config=newconfig)
    newconfig = config.copy()
    newconfig["processing"].append(
        {"NNet_QA": {"acceptance_threshold": 0.5, "model_name": "CantWell"}}
    )
    processed_streams = process_streams(raw_streams.copy(), event, config=newconfig)

    tdir = tempfile.mkdtemp()
    try:
        tfile = os.path.join(tdir, "test.hdf")
        workspace = StreamWorkspace(tfile)
        workspace.addEvent(event)
        workspace.addStreams(event, raw_streams, label="raw")
        workspace.addStreams(event, processed_streams, label="processed")
        stream1 = raw_streams[0]

        # Get metrics from station summary for raw streams
        summary1 = StationSummary.from_config(stream1)
        s1_df_in = summary1.pgms.sort_values(["IMT", "IMC"])
        array1 = s1_df_in["Result"].to_numpy()

        # Compare to metrics from getStreamMetrics for raw streams
        workspace.calcMetrics(eventid, labels=["raw"])
        summary1_a = workspace.getStreamMetrics(
            event.id, stream1[0].stats.network, stream1[0].stats.station, "raw"
        )
        s1_df_out = summary1_a.pgms.sort_values(["IMT", "IMC"])
        array2 = s1_df_out["Result"].to_numpy()

        np.testing.assert_allclose(array1, array2, atol=1e-6, rtol=1e-6)
        workspace.close()
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tdir)


def _test_colocated():
    eventid = "ci38445975"
    datafiles, event = read_data_dir("fdsn", eventid, "*")
    datadir = os.path.split(datafiles[0])[0]
    raw_streams = StreamCollection.from_directory(datadir)
    config_file = os.path.join(datadir, "test_config.yml")
    with open(config_file, "r", encoding="utf-8") as f:
        yaml = YAML()
        yaml.preserve_quotes = True
        config = yaml.load(f)
    processed_streams = process_streams(raw_streams, event, config=config)

    tdir = tempfile.mkdtemp()
    try:
        tfile = os.path.join(tdir, "test.hdf")
        ws = StreamWorkspace(tfile)
        ws.addEvent(event)
        ws.addStreams(event, raw_streams, label="raw")
        ws.addStreams(event, processed_streams, label="processed")
        ws.calcMetrics(eventid, labels=["processed"], config=config)
        stasum = ws.getStreamMetrics(eventid, "CI", "MIKB", "processed")
        np.testing.assert_allclose(
            stasum.get_pgm("duration", "geometric_mean"), 38.94480068
        )
        ws.close()
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tdir)


def _test_vs30_dist_metrics():
    KNOWN_DISTANCES = {
        "epicentral": 5.1,
        "hypocentral": 10.2,
        "rupture": 2.21,
        "rupture_var": np.nan,
        "joyner_boore": 2.21,
        "joyner_boore_var": np.nan,
        "gc2_rx": 2.66,
        "gc2_ry": 3.49,
        "gc2_ry0": 0.00,
        "gc2_U": 34.34,
        "gc2_T": 2.66,
    }
    KNOWN_BAZ = 239.46
    KNOWN_VS30 = 331.47

    eventid = "ci38457511"
    datafiles, event = read_data_dir("fdsn", eventid, "*")
    datadir = os.path.split(datafiles[0])[0]
    raw_streams = StreamCollection.from_directory(datadir)
    config = update_config(os.path.join(datadir, "config_min_freq_0p2.yml"))
    processed_streams = process_streams(raw_streams, event, config=config)
    rupture_file = get_rupture_file(datadir)
    grid_file = os.path.join(datadir, "test_grid.grd")
    config["metrics"]["vs30"] = {
        "vs30": {
            "file": grid_file,
            "column_header": "GlobalVs30",
            "readme_entry": "GlobalVs30",
            "units": "m/s",
        }
    }
    tdir = tempfile.mkdtemp()
    try:
        tfile = os.path.join(tdir, "test.hdf")
        ws = StreamWorkspace(tfile)
        ws.addEvent(event)
        ws.addStreams(event, raw_streams, label="raw")
        ws.addStreams(event, processed_streams, label="processed")
        ws.calcMetrics(
            event.id, rupture_file=rupture_file, labels=["processed"], config=config
        )
        sta_sum = ws.getStreamMetrics(event.id, "CI", "CLC", "processed")

        for dist in sta_sum.distances:
            np.testing.assert_allclose(
                sta_sum.distances[dist], KNOWN_DISTANCES[dist], rtol=0.01
            )
        np.testing.assert_allclose(sta_sum._back_azimuth, KNOWN_BAZ, rtol=0.01)
        np.testing.assert_allclose(
            sta_sum._vs30["vs30"]["value"], KNOWN_VS30, rtol=0.01
        )
        event_df, imc_tables, readme_tables = ws.getTables("processed")
        ws.close()
        check_cols = set(
            [
                "EpicentralDistance",
                "HypocentralDistance",
                "RuptureDistance",
                "RuptureDistanceVar",
                "JoynerBooreDistance",
                "JoynerBooreDistanceVar",
                "GC2_rx",
                "GC2_ry",
                "GC2_ry0",
                "GC2_U",
                "GC2_T",
                "GlobalVs30",
                "BackAzimuth",
            ]
        )
        assert check_cols.issubset(set(readme_tables["Z"]["Column header"]))
        assert check_cols.issubset(set(imc_tables["Z"].columns))
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tdir)


def drop_processing(config, keys):
    newconfig = config.copy()
    newprocess = []
    for pdict in newconfig["processing"]:
        found = False
        for key in keys:
            if key in pdict:
                found = True
                break
        if not found:
            newprocess.append(pdict)
    newconfig["processing"] = newprocess
    return newconfig


def add_processing(config, keys):
    newconfig = config.copy()
    newprocess = []
    for pdict in newconfig["processing"]:
        found = False
        for key in keys:
            if key in pdict:
                found = True
                break
        if not found:
            newprocess.append(pdict)
    newconfig["processing"] = newprocess
    return newconfig


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    # test_stream_params()
    # test_workspace()
    # test_metrics2()
    test_metrics()
    # test_colocated()
    # test_vs30_dist_metrics()
