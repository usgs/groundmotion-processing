#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tempfile
import shutil

import numpy as np
import h5py
from gmprocess.io.asdf.utils import TallyStorage


STORAGE = {
    "QuakeML": {
        "total_bytes": 512,
        "groups": {},
    },
    "Waveforms": {
        "total_bytes": 8 * (300 * 3 + 400 * 3 + 300 * 3),
        "groups": {},
    },
    "AuxiliaryData": {
        "total_bytes": 100 + 200 + 100 + 200 + 300 + 4 * (100 + 200 + 300),
        "groups": {
            "StationMetrics": {
                "total_bytes": 100 + 200,
                "groups": {},
            },
            "WaveformMetrics": {
                "total_bytes": 100 + 200 + 300,
                "groups": {},
            },
            "TraceProcessingParameters": {
                "total_bytes": 4 * (100 + 200 + 300),
                "groups": {},
            },
        },
    },
    "Provenance": {
        "total_bytes": 300 + 400 + 350,
        "groups": {},
    },
}


def generate_workspace():
    """Generate simple HDF5 with ASDF layout for testing."""
    tdir = tempfile.mkdtemp()
    tfilename = os.path.join(tdir, "workspace.h5")
    h5 = h5py.File(tfilename, "w")

    quake_ml = h5.create_dataset("QuakeML", data=np.ones((512,), dtype="uint8"))

    waveforms = h5.create_group("Waveforms")
    st00 = waveforms.create_group("NET.ST00")
    st00.create_dataset(
        "NET.ST00.00.HN1__TSTART_TEND__EV0_label", data=np.ones((300,), dtype="float64")
    )
    st00.create_dataset(
        "NET.ST00.00.HN2__TSTART_TEND__EV0_label", data=np.ones((300,), dtype="float64")
    )
    st00.create_dataset(
        "NET.ST00.00.HNZ__TSTART_TEND__EV0_label", data=np.ones((300,), dtype="float64")
    )
    st00.create_dataset(
        "NET.ST00.00.HN1__TSTART_TEND__EV1_label", data=np.ones((400,), dtype="float64")
    )
    st00.create_dataset(
        "NET.ST00.00.HN2__TSTART_TEND__EV1_label", data=np.ones((400,), dtype="float64")
    )
    st00.create_dataset(
        "NET.ST00.00.HNZ__TSTART_TEND__EV1_label", data=np.ones((400,), dtype="float64")
    )
    st01 = waveforms.create_group("NET.ST01")
    st01.create_dataset(
        "NET.ST01.10.HNE__TSTART_TEND__EV0_label", data=np.ones((300,), dtype="float64")
    )
    st01.create_dataset(
        "NET.ST01.10.HNN__TSTART_TEND__EV0_label", data=np.ones((300,), dtype="float64")
    )
    st01.create_dataset(
        "NET.ST01.10.HNZ__TSTART_TEND__EV0_label", data=np.ones((300,), dtype="float64")
    )

    aux_data = h5.create_group("AuxiliaryData")

    station_metrics = aux_data.create_group("StationMetrics")
    station_metrics.create_dataset("NET.ST00", data=np.ones((100,), dtype="uint8"))
    station_metrics.create_dataset("NET.ST01", data=np.ones((200,), dtype="uint8"))

    waveform_metrics = aux_data.create_group("WaveformMetrics")
    waveform_metrics.create_dataset("NET.ST00_EV0", data=np.ones((100,), dtype="uint8"))
    waveform_metrics.create_dataset("NET.ST00_EV1", data=np.ones((200,), dtype="uint8"))
    waveform_metrics.create_dataset("NET.ST01_EV0", data=np.ones((300,), dtype="uint8"))

    processing_parameters = aux_data.create_group("TraceProcessingParameters")
    processing_parameters.create_dataset(
        "NET.ST00.00.HN1_EV0", data=np.ones((100,), dtype="int32")
    )
    processing_parameters.create_dataset(
        "NET.ST00.00.HN1_EV1", data=np.ones((200,), dtype="int32")
    )
    processing_parameters.create_dataset(
        "NET.ST01.10.HNE_EV0", data=np.ones((300,), dtype="int32")
    )

    provenance = h5.create_group("Provenance")
    provenance.create_dataset("NET.ST00_EV0", data=np.ones((300,), dtype="uint8"))
    provenance.create_dataset("NET.ST00_EV1", data=np.ones((400,), dtype="uint8"))
    provenance.create_dataset("NET.ST01_EV0", data=np.ones((350,), dtype="uint8"))
    h5.close()
    return tfilename


def test_storage():
    tfilename = generate_workspace()
    h5 = h5py.File(tfilename, "r")

    tally = TallyStorage(["AuxiliaryData"])
    total_bytes, groups = tally.compute_storage(h5.items(), store_subtotals=True)
    assert STORAGE == groups

    tally = TallyStorage()
    total_bytes, groups = tally.compute_storage(h5.items(), store_subtotals=False)
    total_bytes_storage = np.sum([STORAGE[group]["total_bytes"] for group in STORAGE])
    assert total_bytes_storage == total_bytes

    tdir = os.path.split(tfilename)[0]
    h5.close()
    shutil.rmtree(tdir)
    return


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_storage()
