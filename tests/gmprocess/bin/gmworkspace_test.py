#!/usr/bin/env pytest

# stdlib imports
import os
import sys
import shutil
import subprocess

# third party imports
import tempfile
import pytest

import numpy as np
import h5py


STORAGE = (
    'Total: 0.288 MB\n'
    '    AuxiliaryData: 0.035 MB\n'
    '        StationMetrics: 0.007 MB\n'
    '        TraceProcessingParameters: 0.023 MB\n'
    '        WaveformMetrics: 0.006 MB\n'
    '    Provenance: 0.010 MB\n'
    '    QuakeML: 0.013 MB\n'
    '    Waveforms: 0.229 MB\n'
)
DESCRIBE = (
    '/AuxiliaryData\n'
    '/AuxiliaryData/StationMetrics\n'
    '    NET.ST00 dims=(2000) type=uint8\n'
    '    NET.ST01 dims=(5000) type=uint8\n'
    '/AuxiliaryData/TraceProcessingParameters\n'
    '    NET.ST00.00.HN1_EV0 dims=(1000) type=int32\n'
    '    NET.ST00.00.HN1_EV1 dims=(2000) type=int32\n'
    '    NET.ST01.10.HNE_EV0 dims=(3000) type=int32\n'
    '/AuxiliaryData/WaveformMetrics\n'
    '    NET.ST00_EV0 dims=(1000) type=uint8\n'
    '    NET.ST00_EV1 dims=(2000) type=uint8\n'
    '    NET.ST01_EV0 dims=(3000) type=uint8\n'
    '/Provenance\n'
    '    NET.ST00_EV0 dims=(3000) type=uint8\n'
    '    NET.ST00_EV1 dims=(4000) type=uint8\n'
    '    NET.ST01_EV0 dims=(3500) type=uint8\n'
    'QuakeML dims=(14000) type=uint8\n'
    '/Waveforms\n'
    '/Waveforms/NET.ST00\n'
    '    NET.ST00.00.HN1__TSTART_TEND__EV0_label dims=(3000) type=float64\n'
    '    NET.ST00.00.HN1__TSTART_TEND__EV1_label dims=(4000) type=float64\n'
    '    NET.ST00.00.HN2__TSTART_TEND__EV0_label dims=(3000) type=float64\n'
    '    NET.ST00.00.HN2__TSTART_TEND__EV1_label dims=(4000) type=float64\n'
    '    NET.ST00.00.HNZ__TSTART_TEND__EV0_label dims=(3000) type=float64\n'
    '    NET.ST00.00.HNZ__TSTART_TEND__EV1_label dims=(4000) type=float64\n'
    '/Waveforms/NET.ST01\n'
    '    NET.ST01.10.HNE__TSTART_TEND__EV0_label dims=(3000) type=float64\n'
    '    NET.ST01.10.HNN__TSTART_TEND__EV0_label dims=(3000) type=float64\n'
    '    NET.ST01.10.HNZ__TSTART_TEND__EV0_label dims=(3000) type=float64\n'
)


def generate_workspace():
    """Generate simple HDF5 with ASDF layout for testing.
    """
    tdir = tempfile.mkdtemp()
    tfilename = os.path.join(tdir, 'workspace.h5')
    h5 = h5py.File(tfilename, 'w')

    h5.create_dataset(
        "QuakeML", data=np.ones((14000,), dtype='uint8'))

    waveforms = h5.create_group("Waveforms")
    st00 = waveforms.create_group("NET.ST00")
    st00.create_dataset("NET.ST00.00.HN1__TSTART_TEND__EV0_label",
                        data=np.ones((3000,), dtype='float64'))
    st00.create_dataset("NET.ST00.00.HN2__TSTART_TEND__EV0_label",
                        data=np.ones((3000,), dtype='float64'))
    st00.create_dataset("NET.ST00.00.HNZ__TSTART_TEND__EV0_label",
                        data=np.ones((3000,), dtype='float64'))
    st00.create_dataset("NET.ST00.00.HN1__TSTART_TEND__EV1_label",
                        data=np.ones((4000,), dtype='float64'))
    st00.create_dataset("NET.ST00.00.HN2__TSTART_TEND__EV1_label",
                        data=np.ones((4000,), dtype='float64'))
    st00.create_dataset("NET.ST00.00.HNZ__TSTART_TEND__EV1_label",
                        data=np.ones((4000,), dtype='float64'))
    st01 = waveforms.create_group("NET.ST01")
    st01.create_dataset("NET.ST01.10.HNE__TSTART_TEND__EV0_label",
                        data=np.ones((3000,), dtype='float64'))
    st01.create_dataset("NET.ST01.10.HNN__TSTART_TEND__EV0_label",
                        data=np.ones((3000,), dtype='float64'))
    st01.create_dataset("NET.ST01.10.HNZ__TSTART_TEND__EV0_label",
                        data=np.ones((3000,), dtype='float64'))

    aux_data = h5.create_group("AuxiliaryData")

    station_metrics = aux_data.create_group("StationMetrics")
    station_metrics.create_dataset(
        "NET.ST00", data=np.ones((2000,), dtype='uint8'))
    station_metrics.create_dataset(
        "NET.ST01", data=np.ones((5000,), dtype='uint8'))

    waveform_metrics = aux_data.create_group("WaveformMetrics")
    waveform_metrics.create_dataset(
        "NET.ST00_EV0", data=np.ones((1000,), dtype='uint8'))
    waveform_metrics.create_dataset(
        "NET.ST00_EV1", data=np.ones((2000,), dtype='uint8'))
    waveform_metrics.create_dataset(
        "NET.ST01_EV0", data=np.ones((3000,), dtype='uint8'))

    processing_parameters = aux_data.create_group("TraceProcessingParameters")
    processing_parameters.create_dataset(
        "NET.ST00.00.HN1_EV0", data=np.ones((1000,), dtype='int32'))
    processing_parameters.create_dataset(
        "NET.ST00.00.HN1_EV1", data=np.ones((2000,), dtype='int32'))
    processing_parameters.create_dataset(
        "NET.ST01.10.HNE_EV0", data=np.ones((3000,), dtype='int32'))

    provenance = h5.create_group("Provenance")
    provenance.create_dataset(
        "NET.ST00_EV0", data=np.ones((3000,), dtype='uint8'))
    provenance.create_dataset(
        "NET.ST00_EV1", data=np.ones((4000,), dtype='uint8'))
    provenance.create_dataset(
        "NET.ST01_EV0", data=np.ones((3500,), dtype='uint8'))
    h5.close()
    return tfilename


def setup_module(module):
    setup_module.tfilename = generate_workspace()
    setup_module.gmworkspace = 'gmworkspace'
    return


def teardown_module(module):
    tdir = os.path.split(setup_module.tfilename)[0]
    shutil.rmtree(tdir)
    return


@pytest.mark.skipif(sys.platform.startswith("win"),
                    reason="Does not work in Windows")
def test_describe():
    tfilename = setup_module.tfilename
    gmworkspace = setup_module.gmworkspace
    output = subprocess.check_output(
        [gmworkspace, '--filename=' + tfilename, '--describe'])
    assert DESCRIBE == output.decode()
    return


@pytest.mark.skipif(sys.platform.startswith("win"),
                    reason="Does not work in Windows")
def test_storage():
    tfilename = setup_module.tfilename
    gmworkspace = setup_module.gmworkspace
    output = subprocess.check_output(
        [gmworkspace, '--filename=' + tfilename, '--compute-storage'])
    assert STORAGE == output.decode()
    return


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_describe()
    test_storage()
